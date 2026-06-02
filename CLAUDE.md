# Telegram Price Alert Bot — Claude Code Instructions

## Project purpose
Python Telegram bot that lets users track product prices on Amazon/Flipkart.
Alerts them when prices drop. Built as a Fiverr portfolio demo.

## Stack
- python-telegram-bot v20 (async, ApplicationBuilder pattern)
- APScheduler (AsyncIOScheduler, NOT BackgroundScheduler)
- aiosqlite for all DB operations (async only — no sync sqlite3)
- httpx + BeautifulSoup4 for scraping
- ScraperAPI for bypassing bot detection (SCRAPERAPI_KEY in .env)
- python-dotenv for config

## File responsibilities
- main.py — build Application, register handlers, start scheduler, run_polling
- bot/handlers.py — CommandHandlers for /start /watch /unwatch /list
- bot/scraper.py — fetch_price(url, platform) → returns float or None
- bot/database.py — init_db(), add_watch(), remove_watch(), get_user_watches(), get_all_active_watches(), update_price()
- bot/scheduler.py — check_prices_job(app): called by APScheduler, fetches all active watches, compares prices, sends alerts

## Key constraints
1. All DB calls must be async (aiosqlite). Never use sqlite3 directly.
2. Scheduler job receives the `app` object (telegram Application) to send messages.
3. ScraperAPI base URL: http://api.scraperapi.com?api_key={KEY}&url={TARGET_URL}
4. Amazon price selector: span.a-price-whole (first match)
5. Flipkart price selector: div._30jeq3 (first match)
6. Price drop threshold: any drop > 0, send alert immediately.
7. Alert format: "📉 Price dropped!\n{product_name}\n₹{old} → ₹{new}\n{url}"
8. /watch accepts either a product name (search Amazon) or a direct Amazon/Flipkart URL
9. Store prices as float with 2 decimal precision.
10. .env vars: TELEGRAM_BOT_TOKEN, SCRAPERAPI_KEY

## DB schema (create in init_db)
CREATE TABLE IF NOT EXISTS watched_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  query TEXT NOT NULL,
  platform TEXT DEFAULT 'amazon',
  product_url TEXT,
  product_name TEXT,
  current_price REAL,
  last_checked DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_active INTEGER DEFAULT 1
);

## Commands and responses
/start → welcome message with usage instructions
/watch [name or url] → scrape price immediately, confirm "Watching: {name} at ₹{price}"
/list → show all active watches with current prices
/unwatch [id] → deactivate by row id (shown in /list)

## Docker
- Dockerfile: python:3.11-slim, copy files, pip install -r requirements.txt, CMD ["python", "main.py"]
- docker-compose.yml: single service, env_file: .env, volumes: ./data:/app/data (for SQLite persistence)
- SQLite path: /app/data/prices.db (so it persists via Docker volume)

## Error handling
- If scrape fails: log warning, skip that item in scheduler run
- If price is None after scrape: don't update DB, don't alert
- Wrap all handlers in try/except, reply with user-friendly error message

## README requirements (write after all code is done)
- 2-3 sentence description
- Tech stack badges
- Screenshot placeholder: ![Demo](assets/demo.gif)
- Setup: 3 steps (clone → .env → docker-compose up)
- Sample /watch and /list output shown as code blocks

## Shared product detection (message handler)
Add a MessageHandler with filters.TEXT that runs on every non-command message.
In handle_shared_message(update, context):
  1. Extract URLs from message text using regex: r'https?://\S+'
  2. Check if any URL matches Amazon or Flipkart domains:
     - Amazon: amzn.in, amazon.in, amzn.to, amazon.com
     - Flipkart: flipkart.com, fkrt.it (short URL)
  3. If match found:
     - Resolve short URLs (amzn.in, amzn.to, fkrt.it) by following redirects with httpx
     - Scrape price immediately
     - Auto-add to watched_items for that user
     - Reply: "✅ Added to watchlist!\n{product_name}\nCurrent price: ₹{price}\nI'll notify you if it drops."
  4. If no URL match: ignore the message silently (don't reply)

Short URL resolution:
  async with httpx.AsyncClient(follow_redirects=True) as client:
      r = await client.head(short_url)
      return str(r.url)  # final resolved URL