import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.database import init_db
from bot.handlers import start_handler, watch_handler, list_handler, unwatch_handler
from bot.scheduler import check_prices_job

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def post_init(application):
    await init_db()
    logger.info("Database initialised")


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]

    app = (
        ApplicationBuilder()
        .token(token)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("watch", watch_handler))
    app.add_handler(CommandHandler("list", list_handler))
    app.add_handler(CommandHandler("unwatch", unwatch_handler))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_prices_job,
        trigger="interval",
        minutes=30,
        args=[app],
        id="price_check",
    )
    scheduler.start()
    logger.info("Scheduler started — checking prices every 30 minutes")

    app.run_polling()


if __name__ == "__main__":
    main()
