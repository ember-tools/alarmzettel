import asyncio
import tempfile
import unittest
from pathlib import Path

import main


class StaticResponseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        root = Path(cls.folder.name)
        (root / "pages" / "hilfe").mkdir(parents=True)
        (root / "pages" / "hilfe" / "index.html").write_text("help page")
        (root / "pages" / "index.html").write_text("start page")
        (root / "index.html").write_text("shell")
        (root / "build.json").write_text("{}")
        (root / "robots.txt").write_text("robots")
        (root / "manifest.webmanifest").write_text("{}")
        cls.previous = main._static
        main._static = root

    @classmethod
    def tearDownClass(cls):
        main._static = cls.previous
        cls.folder.cleanup()

    def test_prerendered_page(self):
        for path in ("hilfe", "hilfe/"):
            response = main.static_response(path)
            self.assertTrue(str(response.path).endswith("pages/hilfe/index.html"))
            self.assertNotIn("x-robots-tag", response.headers)

    def test_start_page_is_public(self):
        for path in ("", "/"):
            response = main.static_response(path)
            self.assertTrue(str(response.path).endswith("pages/index.html"))
            self.assertNotIn("x-robots-tag", response.headers)

    def test_info_moved_to_the_start_page(self):
        response = asyncio.run(main.info())
        self.assertEqual(301, response.status_code)
        self.assertEqual("/", response.headers["location"])

    def test_app_routes_get_the_noindex_shell(self):
        for path in ("alarme", "sitzung/abc", "alarm/1", "index.html", "pages/index.html", "pages/hilfe/index.html", "./index.html",
                     "pages/../index.html", "./pages/hilfe/index.html", "hilfe/../index.html"):
            response = main.static_response(path)
            self.assertTrue(str(response.path).endswith("/index.html") and "pages" not in str(response.path))
            self.assertEqual("noindex, nofollow", response.headers["x-robots-tag"])

    def test_build_info_is_not_cached(self):
        self.assertEqual("no-store", main.static_response("build.json").headers["cache-control"])

    def test_built_files_are_served(self):
        self.assertTrue(str(main.static_response("robots.txt").path).endswith("robots.txt"))

    def test_manifest_has_its_media_type(self):
        response = main.static_response("manifest.webmanifest")
        self.assertEqual("application/manifest+json", response.media_type)

    def test_paths_outside_the_build_fall_back_to_the_shell(self):
        response = main.static_response("../main.py")
        self.assertTrue(str(response.path).endswith("index.html"))


if __name__ == "__main__":
    unittest.main()
