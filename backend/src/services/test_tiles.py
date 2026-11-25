import asyncio
import tempfile
import unittest
from pathlib import Path

import httpx

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import tiles
from services.tiles import (
    CLIENT_MISS_BURST,
    GLOBAL_MISS_BURST,
    MIN_FRESHNESS,
    WAIT_AFTER_FAILURE,
    MissBudget,
    TileCache,
    TileNotAllowed,
    TileRateLimited,
    TileUnavailable,
    allowed,
    column,
    fresh_until,
    row,
)

BERLIN_CENTRE = (14, column(13.4, 14), row(52.52, 14))


class Clock:
    """A clock the test moves by hand."""

    def __init__(self) -> None:
        self.now = 1_000_000.0

    def __call__(self) -> float:
        return self.now


class Upstream:
    """A stand-in for the tile server that counts what it is asked and answers as told."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.status = 200
        self.headers = {"etag": '"v1"', "cache-control": "max-age=60"}
        self.content = b"PNG1"

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(self.status, headers=self.headers, content=self.content)


class TileTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.upstream = Upstream()
        self.clock = Clock()
        self.client = httpx.AsyncClient(transport=httpx.MockTransport(self.upstream))
        self.cache = TileCache(Path(self.folder.name), self.client, self.clock)

    async def asyncTearDown(self):
        await self.cache.close()
        await self.client.aclose()
        self.folder.cleanup()

    async def test_fetches_once_and_serves_from_disk(self):
        first = await self.cache.get(*BERLIN_CENTRE)
        second = await self.cache.get(*BERLIN_CENTRE)
        self.assertEqual(b"PNG1", first)
        self.assertEqual(b"PNG1", second)
        self.assertEqual(1, len(self.upstream.requests))

    async def test_concurrent_requests_share_one_fetch(self):
        results = await asyncio.gather(*(self.cache.get(*BERLIN_CENTRE) for _ in range(5)))
        self.assertEqual([b"PNG1"] * 5, results)
        self.assertEqual(1, len(self.upstream.requests))

    async def test_stale_tile_is_served_and_revalidated_with_etag(self):
        await self.cache.get(*BERLIN_CENTRE)
        self.clock.now += MIN_FRESHNESS + 1
        self.upstream.status = 304
        self.assertEqual(b"PNG1", await self.cache.get(*BERLIN_CENTRE))
        await asyncio.gather(*self.cache._background)
        self.assertEqual('"v1"', self.upstream.requests[-1].headers["if-none-match"])

    async def test_outside_berlin_is_refused_without_asking(self):
        with self.assertRaises(TileNotAllowed):
            await self.cache.get(14, 0, 0)
        with self.assertRaises(TileNotAllowed):
            await self.cache.get(5, 17, 10)
        self.assertEqual([], self.upstream.requests)

    async def test_failed_tile_is_not_asked_again_for_a_while(self):
        self.upstream.status = 500
        with self.assertRaises(TileUnavailable):
            await self.cache.get(*BERLIN_CENTRE)
        with self.assertRaises(TileUnavailable):
            await self.cache.get(*BERLIN_CENTRE)
        self.assertEqual(1, len(self.upstream.requests))
        self.clock.now += WAIT_AFTER_FAILURE + 1
        self.upstream.status = 200
        self.assertEqual(b"PNG1", await self.cache.get(*BERLIN_CENTRE))


    async def test_failed_revalidation_keeps_the_stale_copy_and_backs_off(self):
        await self.cache.get(*BERLIN_CENTRE)
        self.clock.now += MIN_FRESHNESS + 1
        self.upstream.status = 500
        self.assertEqual(b"PNG1", await self.cache.get(*BERLIN_CENTRE))
        await asyncio.gather(*self.cache._background)
        asked = len(self.upstream.requests)
        self.assertEqual(b"PNG1", await self.cache.get(*BERLIN_CENTRE))
        await asyncio.gather(*self.cache._background)
        self.assertEqual(asked, len(self.upstream.requests))

    async def test_misses_beyond_the_client_budget_are_refused_without_asking(self):
        z, x, y = BERLIN_CENTRE
        for offset in range(CLIENT_MISS_BURST):
            await self.cache.get(z, x + offset % 20, y + offset // 20, "1.2.3.4")
        asked = len(self.upstream.requests)
        with self.assertRaises(TileRateLimited):
            await self.cache.get(z, x, y + 10, "1.2.3.4")
        self.assertEqual(asked, len(self.upstream.requests))
        self.assertEqual(b"PNG1", await self.cache.get(z, x, y + 10, "5.6.7.8"))
        self.assertEqual(b"PNG1", await self.cache.get(z, x, y, "1.2.3.4"))


class BudgetTest(unittest.TestCase):
    def test_everyone_shares_one_budget(self):
        clock = Clock()
        budget = MissBudget(clock)
        taken = sum(budget.take(f"client-{n}") for n in range(GLOBAL_MISS_BURST + 10))
        self.assertEqual(GLOBAL_MISS_BURST, taken)

    def test_budget_refills_over_time(self):
        clock = Clock()
        budget = MissBudget(clock)
        while budget.take("one"):
            pass
        clock.now += 60
        self.assertTrue(budget.take("one"))


class RouteTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.upstream = Upstream()
        app = FastAPI()
        app.include_router(tiles.router)
        app.state.tile_cache = TileCache(
            Path(self.folder.name), httpx.AsyncClient(transport=httpx.MockTransport(self.upstream))
        )
        self.client = TestClient(app)

    def tearDown(self):
        self.folder.cleanup()

    def test_tile_is_served_with_browser_cache(self):
        response = self.client.get("/tiles/%s/%s/%s.png" % BERLIN_CENTRE)
        self.assertEqual(200, response.status_code)
        self.assertEqual("image/png", response.headers["content-type"])
        self.assertEqual(tiles.BROWSER_CACHE, response.headers["cache-control"])

    def test_outside_the_box_is_404(self):
        self.assertEqual(404, self.client.get("/tiles/14/0/0.png").status_code)

    def test_unavailable_tile_is_502(self):
        self.upstream.status = 500
        self.assertEqual(502, self.client.get("/tiles/%s/%s/%s.png" % BERLIN_CENTRE).status_code)

    def test_exhausted_budget_is_429(self):
        z, x, y = BERLIN_CENTRE
        codes = [self.client.get(f"/tiles/{z}/{x + n % 20}/{y + n // 20}.png").status_code
                 for n in range(CLIENT_MISS_BURST + 1)]
        self.assertEqual(429, codes[-1])
        response = self.client.get(f"/tiles/{z}/{x}/{y + 9}.png")
        self.assertEqual("10", response.headers["retry-after"])


class FreshnessTest(unittest.TestCase):
    def test_at_least_seven_days(self):
        self.assertEqual(100 + MIN_FRESHNESS, fresh_until(httpx.Headers({"cache-control": "max-age=60"}), 100))

    def test_longer_max_age_wins(self):
        long = MIN_FRESHNESS * 2
        self.assertEqual(100 + long, fresh_until(httpx.Headers({"cache-control": f"max-age={long}"}), 100))

    def test_berlin_box(self):
        self.assertTrue(allowed(*BERLIN_CENTRE))
        self.assertFalse(allowed(19, *BERLIN_CENTRE[1:]))


if __name__ == "__main__":
    unittest.main()
