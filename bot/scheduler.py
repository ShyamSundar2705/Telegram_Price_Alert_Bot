import logging
from telegram import Bot
from bot.database import get_all_active_watches, update_price
from bot.scraper import fetch_price

logger = logging.getLogger(__name__)


async def check_prices_job(app):
    watches = await get_all_active_watches()
    bot: Bot = app.bot

    for item in watches:
        if not item.get("product_url"):
            continue

        new_price, _, _name = await fetch_price(item["product_url"])
        if new_price is None:
            logger.warning("Could not fetch price for item %s, skipping", item["id"])
            continue

        old_price = item.get("current_price")
        await update_price(item["id"], new_price)

        if old_price is not None and new_price < old_price:
            name = item.get("product_name") or item.get("query", "Product")
            message = (
                f"📉 Price dropped!\n"
                f"{name}\n"
                f"₹{old_price:.2f} → ₹{new_price:.2f}\n"
                f"{item['product_url']}"
            )
            try:
                await bot.send_message(chat_id=item["user_id"], text=message)
            except Exception as exc:
                logger.warning("Failed to send alert to %s: %s", item["user_id"], exc)
