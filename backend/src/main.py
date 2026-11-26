import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse

from services.adressen import adressen
from services.sitzung import sitzungen
from services.tiles import TileCache, tile_client
from services.tiles import router as tile_router
from web.app import router
from web.logformat import configure_logging
from web.settings import settings

configure_logging()


async def _aufraeumen():
    """
    Sitzungen laufen 30 Tage nach der letzten Benutzung ab. Das prüft niemand beim Zugriff, also
    geht hier in großem Abstand ein Aufräumer durch – die Frist ist in Tagen gemessen.
    """
    while True:
        await asyncio.sleep(settings.sitzung_sweep_seconds)
        await asyncio.to_thread(sitzungen.aufraeumen)


async def _adressen_holen():
    """
    Fetches the address list when there is none or the copy has aged out.

    Runs beside the server rather than before it: the download is a hundred megabytes and the
    application has to come up whether it succeeds, fails or never finishes. Until it lands,
    completion simply has nothing to offer.
    """
    if not settings.adressen_laden or not adressen.veraltet():
        return
    try:
        anzahl = await asyncio.to_thread(adressen.laden)
        logging.getLogger(__name__).info("Adressliste geladen: %s Einträge", anzahl)
    except Exception as fehler:
        logging.getLogger(__name__).warning("Adressliste nicht geladen: %s", fehler)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    Starts and stops the background work. A restart is the one moment worth walking the whole
    session directory, so it also collects the files an unclean shutdown left behind.
    """
    await asyncio.to_thread(sitzungen.aufraeumen)
    client = tile_client()
    application.state.tile_cache = TileCache(settings.tile_dir, client)
    aufgaben = [asyncio.create_task(_aufraeumen()), asyncio.create_task(_adressen_holen())]
    yield
    for aufgabe in aufgaben:
        aufgabe.cancel()
    await application.state.tile_cache.close()
    await client.aclose()


app = FastAPI(title="Alarmplaner", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials="*" not in settings.origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(tile_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "sitzungen": sitzungen.anzahl(),
            "imSpeicher": sitzungen.im_speicher(),
            "adressen": adressen.bestand()["anzahl"]}


_static = Path(__file__).resolve().parent.parent / "static"


def static_response(path: str) -> FileResponse:
    """Resolves a request outside the API to a file of the built frontend, see `spa`."""
    root = _static.resolve()
    page = (root / "pages" / path.strip("/") / "index.html").resolve()
    if page.is_relative_to(root / "pages") and page != root / "pages" / "index.html" and page.is_file():
        return FileResponse(page)
    candidate = (root / path.strip("/")).resolve()
    if candidate.is_relative_to(root) and candidate != root and candidate.is_file():
        relative = candidate.relative_to(root)
        if relative != Path("index.html") and relative.parts[0] != "pages":
            headers = {"Cache-Control": "no-store"} if relative == Path("build.json") else None
            return FileResponse(candidate, headers=headers)
    return FileResponse(root / "index.html", headers={"X-Robots-Tag": "noindex, nofollow"})


if _static.is_dir():
    app.mount("/assets", StaticFiles(directory=_static / "assets"), name="assets")

    @app.get("/{path:path}")
    async def spa(path: str):
        """
        Everything that is not an API route: a prerendered public page, a built file, or the
        empty shell of the single page app. The shell is never indexed, since its content depends
        on the visitor's own workbook; only the prerendered pages are meant for search engines.
        `build.json` is never cached, so open pages notice a new build.
        """
        return static_response(path)
