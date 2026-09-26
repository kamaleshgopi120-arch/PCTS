"""
backend/test_frontend.py
=============================================================================
Parcel and Courier Tracking System (PCTS) - Phase 19 Verification
Automated Test Suite for Frontend Static Pages and Assets
(Using Python Standard Library html.parser)
=============================================================================
"""

import os
import sys
import re
from html.parser import HTMLParser
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

client = TestClient(app)

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

REQUIRED_PAGES = [
    "index.html",
    "login.html",
    "register.html",
    "book_parcel.html",
    "track.html",
    "dashboard.html",
    "delivery_dashboard.html"
]


class PageInspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.meta_description = None
        self.h1_count = 0
        self.has_style_css = False

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            if attr_dict.get("name") == "description":
                self.meta_description = attr_dict.get("content")
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "link":
            if attr_dict.get("rel") == "stylesheet" and "style.css" in attr_dict.get("href", ""):
                self.has_style_css = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def test_static_files_exist():
    print("=" * 70)
    print("  PHASE 19: FRONTEND STATIC PAGES VERIFICATION")
    print("=" * 70)

    # 1. Verify CSS exists
    css_path = os.path.join(FRONTEND_DIR, "css", "style.css")
    assert os.path.isfile(css_path), f"Missing {css_path}"
    print(f"[PASS] Found CSS stylesheet: {css_path} ({os.path.getsize(css_path)} bytes)")

    # 2. Verify all 7 HTML pages exist and validate SEO / structure
    for page in REQUIRED_PAGES:
        page_path = os.path.join(FRONTEND_DIR, page)
        assert os.path.isfile(page_path), f"Missing page: {page_path}"

        with open(page_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        inspector = PageInspector()
        inspector.feed(html_content)

        # Verify title tag
        assert inspector.title.strip(), f"Page {page} missing <title>"

        # Verify meta description
        assert inspector.meta_description, f"Page {page} missing meta description"

        # Verify exactly one <h1> per SEO standards
        assert inspector.h1_count == 1, f"Page {page} expected exactly 1 <h1>, found {inspector.h1_count}"

        # Verify stylesheet link
        assert inspector.has_style_css, f"Page {page} missing style.css link"

        print(f"[PASS] {page.ljust(25)}: Validated SEO meta, 1x <h1> ('{inspector.title.strip()[:30]}...'), and style.css link")


def test_fastapi_static_mounting():
    print("\n" + "=" * 70)
    print("  PHASE 19: FASTAPI STATIC ROUTE HTTP TEST")
    print("=" * 70)

    # 1. Test CSS via HTTP
    resp = client.get("/static/css/style.css")
    assert resp.status_code == 200, f"Expected 200 for CSS, got {resp.status_code}"
    assert "text/css" in resp.headers.get("content-type", "")
    print(f"[PASS] GET /static/css/style.css -> 200 OK (Content-Type: {resp.headers.get('content-type')})")

    # 2. Test root of static mount (/static/)
    resp = client.get("/static/")
    assert resp.status_code == 200
    assert "Next-Generation" in resp.text
    print("[PASS] GET /static/ (index.html) -> 200 OK")

    # 3. Test each HTML page via FastAPI StaticFiles
    for page in REQUIRED_PAGES:
        resp = client.get(f"/static/{page}")
        assert resp.status_code == 200, f"Failed GET /static/{page}: {resp.status_code}"
        assert "text/html" in resp.headers.get("content-type", "")
        print(f"[PASS] GET /static/{page.ljust(22)} -> 200 OK")

    print("\n" + "=" * 70)
    print("  ALL PHASE 19 FRONTEND TESTS PASSED SUCCESSFULLY! [OK]")
    print("=" * 70)


if __name__ == "__main__":
    test_static_files_exist()
    test_fastapi_static_mounting()
