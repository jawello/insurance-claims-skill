#!/usr/bin/env python3
"""Download a fresh numbered MetLife Cyprus group claim form.

The claim number is stamped in the browser when the form link on the site's
useful documents page is clicked. Fetching the PDF URL directly gives a form
without a number, so this script clicks the link in a headless browser.

Each run produces a new number, so run it once per case.

Usage: download_form.py OUT_DIR [--browser PATH] [--verbose]
Writes OUT_DIR/blank_form_<number>.pdf and prints its path.
"""
import argparse
import pathlib
import re
import sys
import tempfile

from playwright.sync_api import sync_playwright
from pypdf import PdfReader

PAGE_URL = "https://www.metlife.com.cy/en/useful-documents/"
FORM_LINK = 'a[href*="CLAIMS/GROUP_CLAIM_FORM"]'
NUMBER = re.compile(r"\b\d{12}\b")
TIMEOUT_MS = 60_000


def fetch(target, browser_path, verbose):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=browser_path)
        page = browser.new_context(accept_downloads=True).new_page()
        page.goto(PAGE_URL, wait_until="networkidle", timeout=TIMEOUT_MS)
        page.get_by_role("button", name=re.compile(r"^\s*Claims\s*$")).click()
        link = page.locator(FORM_LINK).first
        link.wait_for(state="visible", timeout=TIMEOUT_MS)
        if verbose:
            page.on("request", lambda r: print(r.method, r.url[:120], file=sys.stderr))
        with page.expect_download(timeout=TIMEOUT_MS) as info:
            link.click()
        info.value.save_as(target)
        browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out_dir", type=pathlib.Path)
    parser.add_argument("--browser", help="Chromium executable, if not the one from 'playwright install'")
    parser.add_argument("--verbose", action="store_true", help="print requests made after the click")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.out_dir) as tmp:
        raw = pathlib.Path(tmp) / "form.pdf"
        fetch(raw, args.browser, args.verbose)

        found = NUMBER.findall(PdfReader(raw).pages[0].extract_text() or "")
        if len(found) != 1:
            sys.exit(f"Expected one claim number on page 1, found {found}. The site may have changed.")

        target = args.out_dir / f"blank_form_{found[0]}.pdf"
        if target.exists():
            sys.exit(f"{target} already exists")
        raw.rename(target)
    print(target)


if __name__ == "__main__":
    main()
