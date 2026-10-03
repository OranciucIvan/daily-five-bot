# Daily Five Bot

Telegram bot that asks you for 5 good things from your day and keeps a 7-day report you can share with a friend.

## Features

- Daily fixed-time reminder
- Reply with 5 positives or skip/refuse
- Weekly report
- Optional AI summary via Ollama with fallback
- Old entries auto-deleted after 7 days
- Friend pairing by user ID (set once)

## Setup

```bash
pip install -r requirements.txt
export BOT_TOKEN="..."
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.2:1b"
python bot.py
```

## Commands

- `/start` — register
- `/addfriend <user_id>` — pair with friend (once)
- `/report` — weekly report
