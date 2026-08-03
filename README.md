# Bybit UID Review Telegram Bot

A production-ready Telegram bot for collecting Bybit UID submissions, reviewing them, awarding $1 rewards after approval, and managing withdrawals.

## Features
- Welcome menu with submit/balance/withdraw/statistics actions
- UID submission workflow with duplicate protection
- Admin review panel with approve/reject actions
- Balance and reward tracking
- Withdrawal requests and admin review
- Leaderboard and statistics
- SQLite database with simple migration path
- Logging, error handling, and basic rate limiting

## Setup
1. Install dependencies:
   `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your values.
3. Run the bot:
   `python -m bot.main`

## Environment Variables
- `BOT_TOKEN`: Telegram bot token
- `ADMIN_ID`: Telegram ID of the admin
- `DATABASE_URL`: Database connection string (SQLite default)
- `LOG_LEVEL`: Logging level
- `RATE_LIMIT_PER_MINUTE`: Max user actions per minute
