import os
import json
import logging
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote
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


def _parse_amazon_price(html: str) -> float | None:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.select_one("span.a-price-whole")
    if not tag:
        return None
    try:
        raw = tag.get_text(strip=True).replace(",", "").replace("₹", "").replace("\xa0", "").rstrip(".")
        return round(float(raw), 2)
    except ValueError:
        return None


def _parse_flipkart_price(html: str) -> float | None:
    """Extract price from Flipkart's JSON-LD structured data (stable across redesigns)."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "Product":
                    offers = item.get("offers", {})
                    price = offers.get("price")
                    if price is not None:
                        return round(float(price), 2)
        except (json.JSONDecodeError, ValueError, AttributeError):
            continue
    return None


async def _fetch_flipkart_price(url: str) -> float | None:
    """Use Playwright stealth to render Flipkart and extract price from JSON-LD."""
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
        return _parse_flipkart_price(html)
    except Exception as exc:
        logger.warning("Flipkart Playwright scrape failed for %s: %s", url, exc)
        return None


async def fetch_price(url: str) -> tuple[float | None, str]:
    """Return (price, platform). Price is None if scraping fails."""
    platform = _detect_platform(url)
    try:
        if platform == "flipkart":
            price = await _fetch_flipkart_price(url)
            return price, platform

        # Amazon via ScraperAPI
        scraper_url = _build_scraper_url(url)
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(scraper_url)
            response.raise_for_status()
            price = _parse_amazon_price(response.text)
            return price, platform
    except Exception as exc:
        logger.warning("Scrape failed for %s: %s", url, exc)
        return None, platform
