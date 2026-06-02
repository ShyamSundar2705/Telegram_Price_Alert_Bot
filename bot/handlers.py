import logging
import re
import httpx
from urllib.parse import urlparse
from telegram import Update
from telegram.ext import ContextTypes
from bot.database import add_watch, get_user_watches, remove_watch
from bot.scraper import fetch_price

logger = logging.getLogger(__name__)

SUPPORTED_DOMAINS = {"amazon.in", "amazon.com", "flipkart.com"}
SHORT_DOMAINS = {"amzn.in", "amzn.to", "fkrt.it"}
ALL_WATCHED_DOMAINS = SUPPORTED_DOMAINS | SHORT_DOMAINS | {"amazon.in", "amazon.com"}

_URL_RE = re.compile(r"https?://\S+")


async def _resolve_url(url: str) -> str:
    """Follow redirects and return the final URL (handles amzn.in/amzn.to/fkrt.it)."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.head(url)
            return str(r.url)
    except Exception:
        return url


def _is_url(text: str) -> bool:
    try:
        result = urlparse(text)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Price Alert Bot!\n\n"
        "Commands:\n"
        "/watch <amazon/flipkart URL> — start tracking a product\n"
        "/list — show all tracked products\n"
        "/unwatch <id> — stop tracking a product\n\n"
        "You'll get an alert whenever the price drops!"
    )


async def watch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text("Usage: /watch <Amazon or Flipkart product URL>")
        return

    url = context.args[0]

    if not _is_url(url):
        await update.message.reply_text(
            "Please provide a direct Amazon or Flipkart product URL.\n"
            "Example: /watch https://www.amazon.in/dp/B08N5WRWNW"
        )
        return

    domain = urlparse(url).netloc.replace("www.", "")
    if not any(d in domain for d in SUPPORTED_DOMAINS):
        await update.message.reply_text("Only Amazon and Flipkart URLs are supported.")
        return

    await update.message.reply_text("Fetching current price, please wait...")

    try:
        price, platform = await fetch_price(url)

        if price is None:
            await update.message.reply_text(
                "Could not fetch the price. Please check the URL and try again."
            )
            return

        # Use the last part of the path as a fallback product name
        path_parts = [p for p in urlparse(url).path.split("/") if p]
        product_name = path_parts[-1] if path_parts else url

        await add_watch(
            user_id=user_id,
            query=url,
            platform=platform,
            product_url=url,
            product_name=product_name,
            current_price=price,
        )

        await update.message.reply_text(
            f"✅ Watching: {product_name}\nCurrent price: ₹{price:.2f}\n\n"
            "You'll be notified when the price drops!"
        )
    except Exception as exc:
        logger.exception("Error in watch_handler: %s", exc)
        await update.message.reply_text("Something went wrong. Please try again later.")


async def list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    try:
        watches = await get_user_watches(user_id)

        if not watches:
            await update.message.reply_text(
                "You have no active watches. Use /watch <URL> to start tracking."
            )
            return

        lines = ["📋 Your watched products:\n"]
        for item in watches:
            name = item.get("product_name") or item.get("query", "Unknown")
            price = item.get("current_price")
            price_str = f"₹{price:.2f}" if price is not None else "N/A"
            lines.append(f"[{item['id']}] {name}\n    Price: {price_str}")

        lines.append("\nUse /unwatch <id> to stop tracking.")
        await update.message.reply_text("\n".join(lines))
    except Exception as exc:
        logger.exception("Error in list_handler: %s", exc)
        await update.message.reply_text("Could not retrieve your watch list. Please try again.")


async def unwatch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /unwatch <id>  (get the id from /list)")
        return

    item_id = int(context.args[0])
    try:
        await remove_watch(user_id, item_id)
        await update.message.reply_text(f"✅ Stopped watching item #{item_id}.")
    except Exception as exc:
        logger.exception("Error in unwatch_handler: %s", exc)
        await update.message.reply_text("Could not remove that item. Please try again.")


async def handle_shared_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    urls = _URL_RE.findall(text)

    product_url = None
    for raw_url in urls:
        domain = urlparse(raw_url).netloc.replace("www.", "")
        if any(d in domain for d in SUPPORTED_DOMAINS | SHORT_DOMAINS):
            product_url = raw_url
            break

    if not product_url:
        return

    user_id = str(update.effective_user.id)
    try:
        # Resolve short links before scraping
        domain = urlparse(product_url).netloc.replace("www.", "")
        if any(d in domain for d in SHORT_DOMAINS):
            product_url = await _resolve_url(product_url)

        price, platform = await fetch_price(product_url)
        if price is None:
            await update.message.reply_text(
                "Found a product URL but couldn't fetch its price. "
                "The item may be unavailable."
            )
            return

        path_parts = [p for p in urlparse(product_url).path.split("/") if p]
        product_name = path_parts[-1] if path_parts else product_url

        await add_watch(
            user_id=user_id,
            query=product_url,
            platform=platform,
            product_url=product_url,
            product_name=product_name,
            current_price=price,
        )

        await update.message.reply_text(
            f"✅ Added to watchlist!\n{product_name}\n"
            f"Current price: ₹{price:.2f}\n"
            "I'll notify you if it drops."
        )
    except Exception as exc:
        logger.exception("Error in handle_shared_message: %s", exc)
        await update.message.reply_text("Something went wrong. Please try again later.")
