import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ClauseFlag/1.0; "
        "+https://github.com/clauseflag)"
    ),
    "Accept": "text/html,application/xhtml+xml",
}
_TIMEOUT = 15
_STRIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "form", "noscript"}


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


def scrape_url(url: str) -> str:
    """Fetch a URL and return its main readable text content."""
    _validate_url(url)

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

    text = _extract_text(resp.text)
    if not text:
        raise ValueError(f"No readable content extracted from '{url}'")
    return text
