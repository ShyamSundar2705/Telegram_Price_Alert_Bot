# Telegram Price Alert Bot

A Telegram bot that tracks product prices on Amazon and Flipkart and sends you an alert the moment a price drops — built as a Fiverr portfolio demo.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python) ![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-21.x-green) ![APScheduler](https://img.shields.io/badge/APScheduler-3.x-orange) ![Playwright](https://img.shields.io/badge/Playwright-stealth-purple?logo=playwright) ![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)

![Demo](assets/demo.gif)

## Features

- Track any Amazon India or Flipkart product by URL
- Paste a product link directly into the chat — no command needed
- Prices checked automatically every 30 minutes
- Instant alert when a price drops
- Amazon scraped via ScraperAPI; Flipkart scraped via headless Chromium (Playwright stealth) to bypass bot detection
- Prices and product names extracted from structured data (JSON-LD) for reliability

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/ShyamSundar2705/Telegram_Price_Alert_Bot.git
   cd Telegram_Price_Alert_Bot
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env — fill in TELEGRAM_BOT_TOKEN and SCRAPERAPI_KEY
   ```

3. **Run with Docker**
   ```bash
   docker-compose up -d
   ```

> **Local run (without Docker)**
> ```bash
> pip install -r requirements.txt
> playwright install chromium
> python main.py
> ```

## Commands

| Command | Description |
|---|---|
| `/start` | Show welcome message and usage |
| `/watch <url>` | Start tracking an Amazon or Flipkart product |
| `/list` | Show all active watches with current prices |
| `/unwatch <id>` | Stop tracking a product (use the ID from `/list`) |

You can also just **paste a product URL** directly into the chat — the bot will detect it automatically and add it to your watchlist.

## Usage Examples

### Watch a product
```
/watch https://www.amazon.in/MSI-Laptop/dp/B097PM1MBH/
```
```
✅ Watching: MSI Cyborg 15 Gaming Laptop
Current price: ₹69990.00

You'll be notified when the price drops!
```

### Paste a link directly
```
https://www.flipkart.com/motorola-g35-5g-leaf-green-128-gb/p/itma3ca32cc93927
```
```
✅ Added to watchlist!
MOTOROLA g35 5G (Leaf Green, 128 GB)
Current price: ₹12499.00
I'll notify you if it drops.
```

### List your watches
```
/list
```
```
📋 Your watched products:

[3] MOTOROLA g35 5G (Leaf Green, 128 GB)
    Price: ₹12499.00
[2] Nutritoz Raw Chia Seeds Combo
    Price: ₹137.00
[1] MSI Cyborg 15 Gaming Laptop
    Price: ₹69990.00

Use /unwatch <id> to stop tracking.
```

### Price drop alert
```
📉 Price dropped!
MOTOROLA g35 5G (Leaf Green, 128 GB)
₹12499.00 → ₹11999.00
https://www.flipkart.com/...
```

### Stop tracking
```
/unwatch 3
```
```
✅ Stopped watching item #3.
```

## Tech Stack

| Component | Library |
|---|---|
| Telegram bot | python-telegram-bot 21.x |
| Price check scheduler | APScheduler (AsyncIOScheduler) |
| Database | aiosqlite (SQLite) |
| Amazon scraping | httpx + BeautifulSoup via ScraperAPI |
| Flipkart scraping | Playwright stealth + JSON-LD parsing |
| Config | python-dotenv |
| Deployment | Docker + docker-compose |
