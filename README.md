# Vignan ECAP Attendance Bot

A Telegram bot that fetches and displays student attendance from Vignan College ECAP portal.

## Features

- **Cumulative Attendance**: Shows overall attendance percentage and subject-wise breakdown
- **Today's Attendance**: Displays P/A status for each subject from today's classes
- **Skip Hours Calculator**: Calculates how many hours you can skip while maintaining 75% attendance
- **Auto-refresh**: Quick refresh button to update attendance data

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your bot token in `config.py`:
```python
BOT_TOKEN = "your_telegram_bot_token"
BASE_URL = "https://webprosindia.com/vignanit/"
```

3. Run the bot:
```bash
python bot.py
```

## 🚀 Deployment (24/7 Availability)

Want your bot to run 24/7 without keeping your computer on? Deploy it to the cloud!

**📖 [Read the Complete Deployment Guide →](DEPLOYMENT.md)**

**Quick Deploy Options:**
- **Render** (Recommended) - Free tier, auto-deploys from GitHub
- **Railway** - Fast deployment with $5 free credit
- **PythonAnywhere** - Python-focused hosting

All platforms offer free tiers perfect for this bot. See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step instructions.


## Usage

1. Start the bot: `/start`
2. Login with your credentials: `/login <roll_number> <password>`
3. View your attendance (automatically shown after login)
4. Use the 🔄 Refresh button to update data

## Output Format

```
Hi, Roll Number: 23l31a4391
Total: 113/119 (94.96%)

You can skip 13 hours and still maintain above 75%.

Today's Attendance:
Gen AI: P
DL: PP
MFAR: PPP
CC: PAP

Subject-wise Attendance:
Gen AI: 4/4 (100.00%)
DL: 12/12 (100.00%)
...

Last Updated: 30/12/2025, 12:00:00 AM
```

## Files

- `bot.py` - Telegram bot interface
- `scraper.py` - Web scraping logic with AES encryption
- `attendance_utils.py` - HTML parsing and calculations
- `config.py` - Configuration settings
- `requirements.txt` - Python dependencies

## Technical Details

- **Password Encryption**: Client-side AES-128-CBC encryption
- **Data Fetching**: AjaxPro protocol emulation
- **Attendance Parsing**: Dynamic HTML table parsing
- **Today's Attendance**: Academic Register page scraping

## Requirements

- Python 3.7+
- python-telegram-bot (v20+)
- requests
- beautifulsoup4
- pycryptodome

## License

MIT License
