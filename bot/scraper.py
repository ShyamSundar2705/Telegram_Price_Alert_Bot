import os
import logging
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote

logger = logging.getLogger(__name__)

SCRAPERAPI_BASE = "http://api.scraperapi.com"


def _build_scraper_url(target_url: str) -> str:
    key = os.getenv("SCRAPERAPI_KEY", "")
    return f"{SCRAPERAPI_BASE}?api_key={key}&url={quote(target_url, safe='')}"


def _detect_platform(url: str) -> str:
    if "flipkart.com" in url:
        return "flipkart"
    return "amazon"


def _parse_price(html: str, platform: str) -> float | None:
    soup = BeautifulSoup(html, "html.parser")
    try:
        if platform == "flipkart":
            tag = soup.select_one("div._30jeq3")
        else:
            tag = soup.select_one("span.a-price-whole")

        if not tag:
            return None

        raw = tag.get_text(strip=True).replace(",", "").replace("₹", "").replace("\xa0", "")
        # strip trailing dot that Amazon sometimes includes (e.g. "1,299.")
        raw = raw.rstrip(".")
        return round(float(raw), 2)
    except (ValueError, AttributeError):
        return None


async def fetch_price(url: str) -> tuple[float | None, str]:
    """Return (price, platform). Price is None if scraping fails."""
    platform = _detect_platform(url)
    scraper_url = _build_scraper_url(url)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(scraper_url)
            response.raise_for_status()
            price = _parse_price(response.text, platform)
            return price, platform
    except Exception as exc:
        logger.warning("Scrape failed for %s: %s", url, exc)
        return None, platform
