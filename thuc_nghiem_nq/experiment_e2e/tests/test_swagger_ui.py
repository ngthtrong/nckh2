import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

from playwright.sync_api import sync_playwright


spec = importlib.util.spec_from_file_location(
    "e2e_system", Path(__file__).resolve().parents[1] / "e2e_system.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class SwaggerUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        runner.args = SimpleNamespace(dashboard="http://dashboard.test")
        runner.results = []
        self.page = self.browser.new_page()
        self.page.set_default_timeout(2000)
        self.addCleanup(self.page.close)

    def serve_docs(self, count, delay):
        html = f"""<div id="swagger-ui"></div><script>
        setTimeout(() => {{
            document.getElementById('swagger-ui').innerHTML =
                '<div class="opblock">GET /report</div>'.repeat({count});
        }}, {delay});
        </script>"""
        self.page.route("http://dashboard.test/docs", lambda route: route.fulfill(
            status=200, content_type="text/html", body=html
        ))

    def test_waits_for_operations_rendered_after_network_idle(self):
        self.serve_docs(count=8, delay=1000)
        runner.check_swagger_ui(self.page)
        self.assertEqual(runner.results, [("PASS", "Swagger UI qua proxy dashboard")])

    def test_incomplete_swagger_still_fails(self):
        self.serve_docs(count=7, delay=0)
        runner.check_swagger_ui(self.page)
        self.assertEqual(runner.results, [("FAIL", "Swagger UI qua proxy dashboard")])


if __name__ == "__main__":
    unittest.main()
