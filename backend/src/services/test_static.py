import tempfile
import unittest
from pathlib import Path

import main


class StaticResponseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        root = Path(cls.folder.name)
        (root / "pages" / "info").mkdir(parents=True)
        (root / "pages" / "info" / "index.html").write_text("info page")
        (root / "index.html").write_text("shell")
        (root / "build.json").write_text("{}")
        (root / "robots.txt").write_text("robots")
        cls.previous = main._static
        main._static = root

    @classmethod
    def tearDownClass(cls):
        main._static = cls.previous
        cls.folder.cleanup()

    def test_prerendered_page(self):
        for path in ("info", "info/"):
            response = main.static_response(path)
            self.assertTrue(str(response.path).endswith("pages/info/index.html"))
            self.assertNotIn("x-robots-tag", response.headers)

    def test_app_routes_get_the_noindex_shell(self):
        for path in ("", "sitzung/abc", "alarm/1", "index.html", "pages/info/index.html", "./index.html",
                     "pages/../index.html", "./pages/info/index.html", "info/../index.html"):
            response = main.static_response(path)
            self.assertTrue(str(response.path).endswith("/index.html") and "pages" not in str(response.path))
            self.assertEqual("noindex, nofollow", response.headers["x-robots-tag"])

    def test_build_info_is_not_cached(self):
        self.assertEqual("no-store", main.static_response("build.json").headers["cache-control"])

    def test_built_files_are_served(self):
        self.assertTrue(str(main.static_response("robots.txt").path).endswith("robots.txt"))

    def test_paths_outside_the_build_fall_back_to_the_shell(self):
        response = main.static_response("../main.py")
        self.assertTrue(str(response.path).endswith("index.html"))


if __name__ == "__main__":
    unittest.main()
