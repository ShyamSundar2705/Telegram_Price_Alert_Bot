Build the Telegram Price Alert Bot exactly as described in CLAUDE.md.

Create all files in this order:
1. requirements.txt
2. .env.example (with placeholder values)
3. bot/database.py — init_db() and all CRUD functions using aiosqlite
4. bot/scraper.py — fetch_price(url) using httpx + BeautifulSoup4 via ScraperAPI
5. bot/scheduler.py — check_prices_job(app) that reads all active watches, re-fetches prices, sends alerts on drops
6. bot/handlers.py — /start, /watch, /unwatch, /list handlers
7. main.py — wires everything together: init DB, register handlers, start scheduler, run_polling
8. Dockerfile + docker-compose.yml
9. README.md

After creating all files, run:
  pip install -r requirements.txt
  python -m py_compile main.py bot/handlers.py bot/scraper.py bot/database.py bot/scheduler.py

Fix any import or syntax errors. Do not run the bot (needs real tokens).