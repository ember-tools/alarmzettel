"""The OpenStreetMap tile proxy: tiles fetched once, kept on disk, served to every map.

The OpenStreetMap tile servers ask that clients identify themselves, keep tiles for at least seven
days, never bulk-download and send no more requests than needed. This proxy is that client: every
tile is fetched with the application's own User-Agent and Referer and kept on the data volume, so
the browser never connects to OpenStreetMap. A tile is fresh for as long as the server's
`Cache-Control` or `Expires` says, but never less than seven days. A stale tile is served at once
while it is revalidated in the background with `If-None-Match`. Requests for the same tile that
arrive while it is being fetched wait for that one fetch. Only zoom levels 10 to 18 inside a box
around Berlin are fetched; everything else is refused without asking upstream. At most four tiles
are fetched upstream at once, and cache misses are limited per client and for everyone, so a
request loop over the box gets 429 instead of turning the server into a bulk downloader.
"""

import asyncio
import contextlib
import email.utils
import json
import logging
import math
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

UPSTREAM = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
MIN_ZOOM = 10
MAX_ZOOM = 18
BERLIN = (12.9, 52.25, 13.95, 52.8)
MIN_FRESHNESS = 7 * 24 * 3600
BROWSER_CACHE = "public, max-age=86400"
WAIT_AFTER_FAILURE = 300.0
HOME = "https://alarmzettel.emberbox.app"
MAX_CONCURRENT_FETCHES = 4
GLOBAL_MISS_BURST = 120
GLOBAL_MISSES_PER_SECOND = 0.5
CLIENT_MISS_BURST = 60
CLIENT_MISSES_PER_SECOND = 0.25
logger = logging.getLogger(__name__)

router = APIRouter()


class TileNotAllowed(Exception):
    """A tile outside the zoom levels or the box this proxy serves."""


class TileUnavailable(Exception):
    """A tile neither the cache nor the tile server can provide."""


class TileRateLimited(Exception):
    """A tile that would have to be fetched while the miss budget is used up."""


class MissBudget:
    """Token buckets that limit how many tiles may be fetched upstream.

    Every cache miss takes a token from the bucket shared by everyone and one from the bucket of
    the requesting client. Buckets refill continuously up to their burst size. Maps panning around
    a few districts stay well inside the budget; a loop walking the whole box does not, so the
    server never bulk-downloads from OpenStreetMap on anyone's behalf.
    """

    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        """Start with full buckets."""
        self.clock = clock
        self._buckets: dict[str, tuple[float, float]] = {}

    def take(self, client: str) -> bool:
        """Take a token for `client` and for everyone, or neither when either bucket is empty."""
        now = self.clock()
        everyone = self._level("*", GLOBAL_MISS_BURST, GLOBAL_MISSES_PER_SECOND, now)
        own = self._level(f"client:{client}", CLIENT_MISS_BURST, CLIENT_MISSES_PER_SECOND, now)
        if everyone < 1 or own < 1:
            return False
        self._buckets["*"] = (everyone - 1, now)
        self._buckets[f"client:{client}"] = (own - 1, now)
        if len(self._buckets) > 10_000:
            self._buckets = {key: value for key, value in self._buckets.items() if now - value[1] < 3600}
        return True

    def _level(self, key: str, burst: float, rate: float, now: float) -> float:
        """Return how many tokens a bucket holds right now."""
        level, since = self._buckets.get(key, (burst, now))
        return min(burst, level + (now - since) * rate)


@dataclass
class Tile:
    """A tile's image and how it was fetched."""

    image: bytes
    etag: str | None
    fresh_until: float


def column(longitude: float, z: int) -> int:
    """Return the tile column holding a longitude."""
    return int((longitude + 180) / 360 * 2**z)


def row(latitude: float, z: int) -> int:
    """Return the tile row holding a latitude."""
    radians = math.radians(latitude)
    return int((1 - math.asinh(math.tan(radians)) / math.pi) / 2 * 2**z)


def tile_range(z: int) -> tuple[int, int, int, int]:
    """Return the tile numbers (x from, x to, y from, y to) of the Berlin box at a zoom level."""
    west, south, east, north = BERLIN
    return (*sorted((column(west, z), column(east, z))), *sorted((row(north, z), row(south, z))))


def allowed(z: int, x: int, y: int) -> bool:
    """Tell whether a tile lies within the zoom levels and the Berlin box."""
    if not MIN_ZOOM <= z <= MAX_ZOOM:
        return False
    x_from, x_to, y_from, y_to = tile_range(z)
    return x_from <= x <= x_to and y_from <= y <= y_to


def fresh_until(headers: httpx.Headers, now: float) -> float:
    """Return until when a tile stays fresh: as the server says, but at least seven days."""
    valid = now
    match = re.search(r"max-age=(\d+)", headers.get("cache-control", ""))
    if match:
        valid = now + int(match.group(1))
    elif headers.get("expires"):
        with contextlib.suppress(TypeError, ValueError):
            valid = email.utils.parsedate_to_datetime(headers["expires"]).timestamp()
    return max(valid, now + MIN_FRESHNESS)


def replace(file: Path, content: bytes) -> None:
    """Write a file through a temporary file beside it, so it is never seen half written."""
    temporary = file.with_name(file.name + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(file)


class TileCache:
    """Tiles on disk, fetched from OpenStreetMap when missing and revalidated when stale.

    A tile the tile server could not provide is not asked for again for `WAIT_AFTER_FAILURE`
    seconds: a stale copy is kept that long before the next revalidation, and a missing tile is
    refused that long without asking. During an outage or a block the requests per tile therefore
    stay flat instead of growing with the number of views.
    """

    def __init__(self, directory: Path, client: httpx.AsyncClient, clock: Callable[[], float] = time.time) -> None:
        """Keep tiles below a folder, fetching them with the given client."""
        self.directory = directory
        self.client = client
        self.clock = clock
        self._running: dict[tuple[int, int, int], asyncio.Task[Tile]] = {}
        self._background: set[asyncio.Task[None]] = set()
        self._failed_until: dict[tuple[int, int, int], float] = {}
        self._budget = MissBudget(clock)
        self._fetching = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)

    async def get(self, z: int, x: int, y: int, client: str = "") -> bytes:
        """Return a tile's image from the cache, fetching or revalidating it as needed.

        A miss is refused with `TileRateLimited` once the miss budget of `client` or of everyone
        is used up; a tile already being fetched is waited for without taking from the budget.
        """
        if not allowed(z, x, y):
            raise TileNotAllowed
        cached = self._read(z, x, y)
        if cached is None:
            if self._failed_until.get((z, x, y), 0) > self.clock():
                raise TileUnavailable
            if (z, x, y) not in self._running and not self._budget.take(client):
                raise TileRateLimited
            return (await asyncio.shield(self._fetch_once(z, x, y, None))).image
        if cached.fresh_until < self.clock():
            task = asyncio.ensure_future(self._revalidate(z, x, y, cached))
            self._background.add(task)
            task.add_done_callback(self._background.discard)
        return cached.image

    async def close(self) -> None:
        """Stop every running fetch, before the client they use is closed."""
        tasks = [*self._running.values(), *self._background]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _revalidate(self, z: int, x: int, y: int, old: Tile) -> None:
        """Revalidate a stale tile in the background, logging rather than raising what fails."""
        try:
            await self._fetch_once(z, x, y, old)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Tile %s/%s/%s not revalidated", z, x, y)

    def _fetch_once(self, z: int, x: int, y: int, old: Tile | None) -> asyncio.Task[Tile]:
        """Return the fetch of a tile, starting it unless one is already running."""
        key = (z, x, y)
        running = self._running.get(key)
        if running is not None:
            return running
        task = asyncio.ensure_future(self._fetch(z, x, y, old))
        self._running[key] = task
        task.add_done_callback(lambda _: self._running.pop(key, None))
        return task

    async def _fetch(self, z: int, x: int, y: int, old: Tile | None) -> Tile:
        """Fetch a tile upstream, or confirm the stale copy, and store the result."""
        headers = {"If-None-Match": old.etag} if old and old.etag else {}
        try:
            async with self._fetching:
                response = await self.client.get(UPSTREAM.format(z=z, x=x, y=y), headers=headers)
        except httpx.HTTPError:
            return self._failed(z, x, y, old)
        now = self.clock()
        if response.status_code == 304 and old is not None:
            tile = Tile(old.image, old.etag, fresh_until(response.headers, now))
        elif response.status_code == 200:
            tile = Tile(response.content, response.headers.get("etag"), fresh_until(response.headers, now))
        else:
            return self._failed(z, x, y, old)
        self._failed_until.pop((z, x, y), None)
        self._write(z, x, y, tile)
        return tile

    def _failed(self, z: int, x: int, y: int, old: Tile | None) -> Tile:
        """Keep a stale copy for a while after a failed fetch, or refuse a missing tile for one."""
        until = self.clock() + WAIT_AFTER_FAILURE
        if old is None:
            now = self.clock()
            self._failed_until = {key: value for key, value in self._failed_until.items() if value > now}
            self._failed_until[(z, x, y)] = until
            raise TileUnavailable
        tile = Tile(old.image, old.etag, until)
        self._write(z, x, y, tile)
        return tile

    def _path(self, z: int, x: int, y: int) -> Path:
        """Return where a tile's image is kept."""
        return self.directory / str(z) / str(x) / f"{y}.png"

    def _read(self, z: int, x: int, y: int) -> Tile | None:
        """Read a tile from disk; a missing, broken or incomplete one counts as not there."""
        image = self._path(z, x, y)
        try:
            meta = json.loads(image.with_suffix(".json").read_text())
            return Tile(image.read_bytes(), meta.get("etag"), float(meta["freshUntil"]))
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _write(self, z: int, x: int, y: int, tile: Tile) -> None:
        """Write a tile to disk, each file through a temporary one, so a crash breaks neither."""
        image = self._path(z, x, y)
        image.parent.mkdir(parents=True, exist_ok=True)
        replace(image, tile.image)
        replace(image.with_suffix(".json"), json.dumps({"etag": tile.etag, "freshUntil": tile.fresh_until}).encode())


def tile_client() -> httpx.AsyncClient:
    """Return the client tiles are fetched with, named as the tile usage policy asks."""
    return httpx.AsyncClient(
        timeout=10.0,
        headers={"User-Agent": f"alarmzettel (+{HOME})", "Referer": f"{HOME}/"},
    )


@router.get("/tiles/{z}/{x}/{y}.png")
async def tile(z: int, x: int, y: int, request: Request) -> Response:
    """Return a map tile of Berlin from the cache, fetching it from OpenStreetMap when needed."""
    cache: TileCache = request.app.state.tile_cache
    try:
        image = await cache.get(z, x, y, request.client.host if request.client else "")
    except TileNotAllowed as error:
        raise HTTPException(status_code=404, detail="Diese Kachel gibt es hier nicht.") from error
    except TileUnavailable as error:
        raise HTTPException(status_code=502, detail="Die Kachel ist gerade nicht ladbar.") from error
    except TileRateLimited as error:
        raise HTTPException(
            status_code=429, detail="Zu viele neue Kacheln auf einmal.", headers={"Retry-After": "10"}
        ) from error
    return Response(content=image, media_type="image/png", headers={"Cache-Control": BROWSER_CACHE})
