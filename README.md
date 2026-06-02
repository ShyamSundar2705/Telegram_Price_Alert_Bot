# Telegram Price Alert Bot

A Telegram bot that tracks product prices on Amazon and Flipkart and alerts you the moment a price drops — built as a Fiverr portfolio demo.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python) ![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-20.x-green) ![APScheduler](https://img.shields.io/badge/APScheduler-3.x-orange) ![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)

![Demo](assets/demo.gif)

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/youruser/telegram-price-alert-bot.git
   cd telegram-price-alert-bot
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and fill in TELEGRAM_BOT_TOKEN and SCRAPERAPI_KEY
   ```

3. **Run with Docker**
   ```bash
   docker-compose up -d
   ```

## Usage

### Watch a product
```
/watch https://www.amazon.in/dp/B08N5WRWNW
```
```
✅ Watching: B08N5WRWNW
Current price: ₹1,299.00

You'll be notified when the price drops!
```

### List your watches
```
/list
```
```
📋 Your watched products:

[1] B08N5WRWNW
    Price: ₹1,299.00
[2] some-flipkart-product
    Price: ₹899.00

Use /unwatch <id> to stop tracking.
```

### Stop tracking
```
/unwatch 1
```
