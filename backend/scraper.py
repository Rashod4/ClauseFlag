import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
_TIMEOUT = 15
_STRIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "form", "noscript"}
_MIN_USEFUL_TEXT_LENGTH = 200


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Invalid URL scheme '{parsed.scheme}': only http and https are supported"
        )
    if not parsed.netloc or "." not in parsed.netloc:
        raise ValueError(f"Invalid URL structure: '{url}' has no valid domain")
    return url


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup.find_all(_STRIP_TAGS):
        tag.decompose()

    main = soup.find("article") or soup.find("main") or soup.find("body")
    if main is None:
        raise ValueError("Could not locate readable content in the page")

    text = main.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fetch_with_requests(url: str) -> str:
    """Fast path: static HTTP fetch."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
    except requests.Timeout:
        raise RuntimeError("URL took too long to respond") from None
    except requests.RequestException as exc:
        raise RuntimeError(f"Network error while fetching '{url}': {exc}") from exc

    if resp.status_code != 200:
        raise RuntimeError(
            f"Non-200 response ({resp.status_code}) from '{url}'"
        )
    return _extract_text(resp.text)


def _fetch_with_playwright(url: str) -> str:
    """Slow path: headless browser for JS-rendered pages.

    Runs in a separate thread to avoid conflicts between Playwright's
    greenlet-based sync API and uvicorn's running asyncio event loop.
    """
    import concurrent.futures

    def _run() -> str:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=30_000)
                html = page.content()
            finally:
                browser.close()
        return _extract_text(html)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_run)
        return future.result(timeout=45)


def scrape_url(url: str) -> str:
    """Fetch a URL and return its main readable text content.

    Tries a fast static fetch first; falls back to a headless browser
    when the page relies on JavaScript to render its content.
    """
    _validate_url(url)

    text = ""
    try:
        text = _fetch_with_requests(url)
    except (ValueError, RuntimeError):
        pass

    if len(text) < _MIN_USEFUL_TEXT_LENGTH:
        try:
            text = _fetch_with_playwright(url)
        except Exception as exc:
            if not text:
                raise ValueError(
                    f"No readable content extracted from '{url}'"
                ) from exc

    if not text:
        raise ValueError(f"No readable content extracted from '{url}'")
    return text
