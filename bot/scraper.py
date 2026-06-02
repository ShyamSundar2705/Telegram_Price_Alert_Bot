import os
import json
import logging
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

logger = logging.getLogger(__name__)

SCRAPERAPI_BASE = "http://api.scraperapi.com"
_FK_STEALTH = Stealth()


def _detect_platform(url: str) -> str:
    if "flipkart.com" in url:
        return "flipkart"
    return "amazon"


def _build_scraper_url(target_url: str) -> str:
    key = os.getenv("SCRAPERAPI_KEY", "")
    return f"{SCRAPERAPI_BASE}?api_key={key}&url={quote(target_url, safe='')}"


def _amazon_name_from_url(url: str) -> str:
    """Best-effort name from the URL slug (e.g. MSI-Laptop-... → MSI Laptop ...)."""
    parts = [p for p in urlparse(url).path.split("/") if p and p != "dp"]
    for part in parts:
        if not part.startswith("B0") and len(part) > 6:
            return part.replace("-", " ").strip()
    return parts[0].replace("-", " ") if parts else "Unknown"


def _parse_amazon(html: str, url: str) -> tuple[float | None, str]:
    soup = BeautifulSoup(html, "html.parser")

    # Price
    price_tag = soup.select_one("span.a-price-whole")
    price = None
    if price_tag:
        try:
            raw = price_tag.get_text(strip=True).replace(",", "").replace("₹", "").replace("\xa0", "").rstrip(".")
            price = round(float(raw), 2)
        except ValueError:
            pass

    # Name — prefer page title element, fall back to URL slug
    name_tag = soup.select_one("span#productTitle")
    if name_tag:
        name = name_tag.get_text(strip=True)
    else:
        name = _amazon_name_from_url(url)

    return price, name


def _parse_flipkart(html: str) -> tuple[float | None, str]:
    """Extract price and name from Flipkart's JSON-LD structured data."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "Product":
                    name = item.get("name", "Unknown")
                    offers = item.get("offers", {})
                    raw_price = offers.get("price")
                    price = round(float(raw_price), 2) if raw_price is not None else None
                    return price, name
        except (json.JSONDecodeError, ValueError, AttributeError):
            continue
    return None, "Unknown"


async def _fetch_flipkart(url: str) -> tuple[float | None, str]:
    """Use Playwright stealth to render Flipkart and extract price + name from JSON-LD."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="en-IN",
                viewport={"width": 1366, "height": 768},
            )
            page = await ctx.new_page()
            await _FK_STEALTH.apply_stealth_async(page)
            await page.goto("https://www.flipkart.com/", wait_until="domcontentloaded", timeout=20000)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            html = await page.content()
            await browser.close()
        return _parse_flipkart(html)
    except Exception as exc:
        logger.warning("Flipkart Playwright scrape failed for %s: %s", url, exc)
        return None, "Unknown"


async def fetch_price(url: str) -> tuple[float | None, str, str]:
    """Return (price, platform, product_name). Price is None if scraping fails."""
    platform = _detect_platform(url)
    try:
        if platform == "flipkart":
            price, name = await _fetch_flipkart(url)
            return price, platform, name

        # Amazon via ScraperAPI
        scraper_url = _build_scraper_url(url)
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(scraper_url)
            response.raise_for_status()
            price, name = _parse_amazon(response.text, url)
            return price, platform, name
    except Exception as exc:
        logger.warning("Scrape failed for %s: %s", url, exc)
        return None, platform, "Unknown"
