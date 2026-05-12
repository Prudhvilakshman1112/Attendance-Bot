# 📘 Vignan ECAP Attendance Bot — Complete Project Knowledge

> **Purpose of this document**: Interview preparation reference covering every aspect of this project — what it is, why it was built, how it works internally, the tech stack rationale, architecture, deployment, challenges faced, and potential improvements.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement & Motivation](#2-problem-statement--motivation)
3. [Tech Stack & Justification](#3-tech-stack--justification)
4. [System Architecture](#4-system-architecture)
5. [Project File Structure](#5-project-file-structure)
6. [Detailed Module Breakdown](#6-detailed-module-breakdown)
7. [Complete Workflow — End to End](#7-complete-workflow--end-to-end)
8. [Security Considerations](#8-security-considerations)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Challenges Faced & Solutions](#10-challenges-faced--solutions)
11. [Key Interview Q&A](#11-key-interview-qa)
12. [Future Improvements](#12-future-improvements)

---

## 1. Project Overview

**Project Name**: Vignan ECAP Attendance Bot  
**Type**: Telegram Bot (Backend automation / Web Scraping)  
**Language**: Python 3.11  
**Deployment**: Render (Free Tier) via Webhook  
**Live URL**: `https://vignan-attendance-bot.onrender.com`

### What It Does

This is a **Telegram Bot** that allows students of Vignan College to instantly check their attendance from the college's ECAP (Education Campus Automation Portal) — right inside Telegram, without opening a browser or navigating the slow college portal.

### Key Features

| Feature | Description |
|---------|-------------|
| **Cumulative Attendance** | Overall attendance % and subject-wise breakdown |
| **Today's Attendance** | Real-time P (Present) / A (Absent) status per subject for the current day |
| **Skip-Hours Calculator** | Calculates how many classes you can safely skip while staying above 75% |
| **Refresh Button** | Inline button to re-fetch latest data without re-entering credentials |
| **Multi-Account Support** | A single Telegram user can check attendance for multiple roll numbers |
| **Credential Persistence** | Saved to disk (JSON) so the Refresh button survives server restarts |
| **Auto-Delete Credentials** | The message containing the password is deleted immediately for security |

---

## 2. Problem Statement & Motivation

### The Problem

Vignan College uses **ECAP** (hosted on `webprosindia.com`) for attendance management. Students face these issues:

1. **Slow & clunky portal** — The web UI is old, built with ASP.NET WebForms, and loads slowly.
2. **No mobile-friendly interface** — Checking attendance on mobile is frustrating.
3. **No quick summary** — Students have to navigate multiple pages to see subject-wise data.
4. **No "today's attendance" view** — The portal doesn't show today's P/A status in a simple format.
5. **No skip-hour calculator** — Students manually calculate how many classes they can afford to miss.

### The Solution

Build a **Telegram Bot** that:
- Accepts roll number + password
- Logs into the ECAP portal programmatically (web scraping)
- Extracts attendance data from the HTML responses
- Formats it into a clean, emoji-rich Telegram message
- Provides a one-tap Refresh button for re-checking

### Why a Telegram Bot?

| Alternative | Why Not |
|-------------|---------|
| Mobile App | Requires Play Store approval, APK distribution, platform-specific code |
| Web App | Needs frontend + hosting; students must remember a URL |
| WhatsApp Bot | WhatsApp Business API is paid and complex |
| **Telegram Bot** ✅ | Free API, instant setup, cross-platform, inline buttons, no app install needed |

---

## 3. Tech Stack & Justification

### Core Technologies

| Technology | Role | Why This Choice |
|------------|------|-----------------|
| **Python 3.11** | Primary language | Best ecosystem for web scraping (requests, BeautifulSoup). Fast prototyping. Ideal for bot development. |
| **python-telegram-bot v20+** | Telegram Bot framework | Official, well-documented, async-native, supports inline keyboards and callback queries |
| **Requests** | HTTP client for scraping | Simple, session-based, handles cookies/redirects — perfect for form-based login flows |
| **BeautifulSoup4** | HTML parser | Industry standard for parsing messy HTML. Handles broken markup from ASP.NET WebForms gracefully |
| **PyCryptodome** | AES encryption | The ECAP portal encrypts passwords client-side with AES-128-CBC before sending. We must replicate this. |
| **Flask** | Web framework (webhook server) | Lightweight — only needed to expose `/webhook` and `/ping` endpoints. No need for Django's overhead |
| **Gunicorn** | WSGI HTTP server | Production-grade server for Flask. Required by Render for deployment |
| **python-dotenv** | Environment variables | Loads `.env` file for local development; keeps secrets out of source code |

### Why Python Over Other Languages?

| Language | Limitation for This Project |
|----------|----------------------------|
| JavaScript/Node.js | Less mature scraping libraries; Cheerio doesn't handle ASP.NET ViewState well |
| Java | Verbose; overkill for a simple scraping bot |
| Go | Poor HTML parsing ecosystem compared to Python |
| **Python** ✅ | Best scraping ecosystem (requests + BS4), excellent Telegram bot libraries, rapid development |

### Why Requests + BeautifulSoup Over Selenium?

| Approach | Pros | Cons |
|----------|------|------|
| **Selenium** | Handles JavaScript-rendered pages | Heavy (needs browser binary), slow, resource-intensive, hard to deploy on free tiers |
| **Requests + BS4** ✅ | Lightweight, fast, no browser needed, easy to deploy | Must reverse-engineer AJAX calls manually |

We chose Requests + BS4 because the ECAP portal uses **AjaxPro** (server-side rendering with AJAX calls) — not a modern SPA. All data is fetched via predictable HTTP POST requests that we can replicate.

---

## 4. System Architecture

### High-Level Architecture

```
┌──────────────┐       ┌──────────────────┐       ┌─────────────────────┐
│   Student    │       │   Telegram API   │       │   Render Server     │
│  (Telegram)  │──────▶│   (Cloud)        │──────▶│   (Flask + Bot)     │
│              │◀──────│                  │◀──────│                     │
└──────────────┘       └──────────────────┘       │  ┌───────────────┐  │
                                                  │  │  bot.py       │  │
                                                  │  │  (Flask +     │  │
                                                  │  │   PTB App)    │  │
                                                  │  └───────┬───────┘  │
                                                  │          │          │
                                                  │  ┌───────▼───────┐  │
                                                  │  │  scraper.py   │  │
                                                  │  │  (ECAP Login  │  │
                                                  │  │   + Scrape)   │──┼──▶ ECAP Portal
                                                  │  └───────┬───────┘  │    (webprosindia.com)
                                                  │          │          │
                                                  │  ┌───────▼───────┐  │
                                                  │  │ attendance_   │  │
                                                  │  │ utils.py      │  │
                                                  │  │ (Parse + Fmt) │  │
                                                  │  └───────────────┘  │
                                                  └─────────────────────┘
```

### Threading Architecture (Critical Design Decision)

The bot uses a **hybrid sync + async** architecture because:

- **Flask** is synchronous (WSGI)
- **python-telegram-bot v20** is fully async
- **Webhook mode** requires Flask to receive HTTP POSTs from Telegram

**Solution**: A dedicated background thread runs an `asyncio` event loop with a queue:

```
Main Thread (Flask/Gunicorn)          Background Thread (asyncio)
┌─────────────────────────┐          ┌─────────────────────────┐
│  POST /webhook           │          │  asyncio event loop      │
│  ↓                       │          │  ↓                       │
│  Parse JSON → Update     │──queue──▶│  process_update()        │
│  Put in asyncio.Queue    │          │  ↓                       │
│  Return "ok" 200         │          │  Call handler (start,     │
│                          │          │   handle_credentials,     │
│  GET /ping               │          │   refresh_button_handler) │
│  Return "pong" 200       │          │  ↓                       │
│                          │          │  scraper.login()          │
│  GET /                   │          │  scraper.get_attendance() │
│  Return health check     │          │  Send reply to user       │
└─────────────────────────┘          └─────────────────────────┘
```

**Why single worker?** Gunicorn is configured with `workers = 1` because the async event loop thread must live in the same process that handles webhook requests. Multiple workers would create multiple isolated event loops.

---

## 5. Project File Structure

```
d:\attendence\
├── bot.py                  # Main entry point — Flask app + Telegram handlers
├── scraper.py              # ECAPScraper class — login, fetch attendance, AES encryption
├── attendance_utils.py     # HTML parsing, skip-hour calculation, message formatting
├── config.py               # Configuration — BOT_TOKEN, BASE_URL (from env vars)
├── requirements.txt        # Python dependencies (7 packages)
├── gunicorn.conf.py        # Gunicorn server config (1 worker, 30s timeout)
├── render.yaml             # Render IaC deployment blueprint
├── Procfile                # Process declaration for Render/Heroku
├── runtime.txt             # Python version specification (3.11.7)
├── .env.example            # Template for environment variables
├── .gitignore              # Ignores .env, __pycache__, debug files, credentials JSON
├── README.md               # Project documentation
├── RENDER_DEPLOYMENT.md    # Step-by-step deployment guide
└── TIMESTAMP_FIX.md        # Documentation of IST timezone bug fix
```

---

## 6. Detailed Module Breakdown

### 6.1 `config.py` — Configuration Management

```python
BASE_URL = os.getenv("BASE_URL", "https://webprosindia.com/vignanit/")
LOGIN_URL = BASE_URL + "Login.aspx"
BOT_TOKEN = os.getenv("BOT_TOKEN", "<fallback>")
```

- Uses `python-dotenv` to load `.env` file in development
- Falls back to defaults if env vars are missing
- All URLs are derived from a single `BASE_URL`

### 6.2 `scraper.py` — The Web Scraping Engine

This is the **most technically complex** module. It reverse-engineers the ECAP portal's authentication and data retrieval.

#### Class: `ECAPScraper`

**`__init__`**: Creates a `requests.Session()` (maintains cookies across requests, essential for authenticated scraping) with a browser-like User-Agent header.

**`_encrypt_password(password)`** — AES-128-CBC Encryption:
- The ECAP portal uses **client-side password encryption** via CryptoJS
- Before the login form is submitted, JavaScript encrypts the password using AES-128-CBC
- Key and IV are both `8701661282118308` (extracted by reverse-engineering the portal's JavaScript)
- We replicate this with PyCryptodome:

```python
key = b'8701661282118308'
iv  = b'8701661282118308'
cipher = AES.new(key, AES.MODE_CBC, iv)
padded = pad(password.encode('utf-8'), AES.block_size)  # PKCS7 padding
encrypted = cipher.encrypt(padded)
return base64.b64encode(encrypted).decode('utf-8')
```

**`login(username, password)`** — Two-Step Login:

1. **GET the login page** → Parse HTML with BeautifulSoup → Extract all hidden form fields (ASP.NET ViewState, EventValidation, etc.)
2. **Encrypt the password** using AES-128-CBC
3. **POST the form** with hidden fields + credentials to the form's action URL
4. **Detect success/failure** by checking if the response still contains the login form (`txtId2` field)

**`get_attendance()`** — AjaxPro Protocol Emulation:

This is the most complex part. The ECAP portal uses **AjaxPro** (an old ASP.NET AJAX framework):

1. **GET the attendance page** (`StudentAttendance.aspx`)
2. **Extract the Ajax script URL** from a `<script>` tag (e.g., `ajax/StudentAttendance.ashx`)
3. **Extract the roll number** from a hidden input field
4. **POST to the Ajax endpoint** with:
   - Custom header: `X-AjaxPro-Method: ShowAttendance`
   - Body format: `rollNo=<value>\r\nfromDate=\r\ntoDate=\r\nexcludeothersubjects=false`
5. **Parse the response** which can be in multiple formats:
   - JavaScript string literal (single-quoted HTML)
   - JSON wrapped in `/*JSON*/.../*JSON*/` comments
   - Plain JSON with a `value` field

**`get_todays_attendance()`** — Academic Register Scraping:

1. **GET the Academic Register page** (`studentacadamicregister.aspx?scrid=2`)
2. **Find the attendance table** inside `divRegister` (identifies it by having >10 rows and date-like headers)
3. **Locate today's column** by matching `DD/MM` format with current IST date
4. **Extract P/A status** for each subject from the matching column

### 6.3 `attendance_utils.py` — Data Processing

**`parse_attendance(html_content)`**:
- Parses the HTML table (class `cellBorder`) returned by the AjaxPro call
- Extracts: Subject Name, Classes Conducted, Classes Attended, Percentage
- Calculates overall attendance percentage
- Generates IST timestamp

**`calculate_skip_hours(total_present, total_classes, target=75)`**:
- If attendance ≥ 75%: Calculates max skippable hours using formula:
  `max_total = total_present / 0.75` → `skippable = max_total - total_classes`
- If attendance < 75%: Calculates hours needed using formula:
  `needed = (0.75 × total_classes - total_present) / (1 - 0.75)`

**`format_message(data, username, todays_attendance)`**:
- Builds a rich Telegram message with emojis and Markdown
- Color-coded indicators: 🟢 (≥90%), 🟡 (≥75%), 🔴 (<75%)

### 6.4 `bot.py` — The Main Application

This file contains **two applications running together**:

#### A. Flask Web Server (Webhook Receiver)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhook` | POST | Receives Telegram updates, queues them for async processing |
| `/` | GET | Health check — returns "Attendance Bot is Running ✅" |
| `/ping` | GET | Lightweight keep-alive endpoint |

#### B. Telegram Bot Handlers

| Handler | Trigger | Action |
|---------|---------|--------|
| `start` | `/start` command | Sends welcome message with usage instructions |
| `handle_credentials` | Any text message matching `<username> <password>` | Logs in, scrapes data, sends formatted attendance |
| `refresh_button_handler` | "🔄 Refresh" inline button click | Re-fetches attendance using stored credentials |
| `cancel` | `/cancel` command | Clears all stored credentials for the user |

#### C. Credential Persistence System

- Credentials are stored in `user_credentials.json` on disk
- Thread-safe access via `threading.Lock()`
- Structure: `{ "telegram_user_id": { "roll_number": "password" } }`
- Functions: `store_user_cred()`, `get_user_cred()`, `get_all_user_creds()`, `clear_user_creds()`

#### D. Keep-Alive Thread

Render's free tier spins down after 15 min of inactivity. A daemon thread pings `/ping` every 10 minutes via `urllib.request` to prevent this.

---

## 7. Complete Workflow — End to End

### Step-by-Step: User Checks Attendance

```
1. USER sends "23L31A4391 mypassword" to the bot on Telegram

2. Telegram API forwards this as an HTTP POST to:
   https://vignan-attendance-bot.onrender.com/webhook

3. Flask receives the POST in webhook() function
   → Parses JSON into a Telegram Update object
   → Puts it into the asyncio.Queue

4. Background thread picks up the Update
   → Routes to handle_credentials() handler

5. handle_credentials():
   a. Splits text into username="23L31A4391", password="mypassword"
   b. DELETES the original message (security — removes password from chat)
   c. Sends status: "🔐 Logging in..."

6. ECAPScraper.login():
   a. GET https://webprosindia.com/vignanit/Login.aspx
   b. Parse HTML → extract hidden fields (__VIEWSTATE, __EVENTVALIDATION, etc.)
   c. Encrypt password with AES-128-CBC (key: 8701661282118308)
   d. POST form data to login endpoint
   e. Check response — if login form is still present → failure
   f. Return success (session cookies are now authenticated)

7. ECAPScraper.get_attendance():
   a. GET StudentAttendance.aspx (authenticated via session cookies)
   b. Extract Ajax script URL and roll number from HTML
   c. POST to AjaxPro endpoint with X-AjaxPro-Method header
   d. Parse response (JavaScript string / JSON) → return HTML table

8. parse_attendance():
   a. Parse HTML table with BeautifulSoup
   b. Extract each row: Subject, Conducted, Attended, Percentage
   c. Calculate overall percentage and IST timestamp

9. ECAPScraper.get_todays_attendance():
   a. GET studentacadamicregister.aspx
   b. Find the large attendance grid table
   c. Match today's date column (IST-aware)
   d. Extract P/A status per subject

10. format_message():
    a. Build formatted string with emojis and Markdown
    b. Include skip-hours calculation
    c. Add today's P/A breakdown

11. store_user_cred():
    a. Save credentials to user_credentials.json for refresh feature

12. Send the formatted message with "🔄 Refresh" inline button
    → User sees their complete attendance report
```

### Step-by-Step: User Clicks Refresh

```
1. User clicks "🔄 Refresh" button
2. Telegram sends callback_query with data "refresh_23L31A4391"
3. refresh_button_handler() extracts username from callback data
4. Looks up stored password from user_credentials.json
5. Repeats steps 6-12 from above
6. Edits the SAME message with updated data
```

---

## 8. Security Considerations

| Concern | Mitigation |
|---------|------------|
| Password visible in chat | Bot immediately deletes the user's message containing credentials |
| Credential storage | Stored in a JSON file on server; user can clear with `/cancel` |
| Password in transit to bot | Telegram uses end-to-end TLS; webhook uses HTTPS |
| Password sent to ECAP | Encrypted with AES-128-CBC before transmission (matching portal's own encryption) |
| Bot token exposure | Loaded from environment variables, not hardcoded in production |
| `.gitignore` protections | `user_credentials.json`, `.env`, and debug files are excluded from Git |

### Limitations (Be Honest in Interviews)

- Credentials are stored in **plaintext JSON** on the server (not encrypted at rest)
- A proper production system would use an encrypted database or a secrets manager
- The AES key is hardcoded (but it's the portal's own key, not ours)

---

## 9. Deployment Architecture

### Platform: Render (Free Tier)

```
GitHub Repository
       │
       ▼ (auto-deploy on push)
┌─────────────────────────────────────┐
│           Render Platform            │
│                                      │
│  Build: pip install -r requirements  │
│  Start: gunicorn -c gunicorn.conf.py │
│         bot:app                      │
│                                      │
│  Environment Variables:              │
│  ├── BOT_TOKEN                       │
│  ├── BASE_URL                        │
│  └── RENDER_EXTERNAL_URL             │
│                                      │
│  Endpoints:                          │
│  ├── GET  /        → Health check    │
│  ├── GET  /ping    → Keep-alive      │
│  └── POST /webhook → Telegram input  │
└─────────────────────────────────────┘
```

### Why Webhook Mode Instead of Polling?

| Polling Mode | Webhook Mode |
|-------------|--------------|
| Bot continuously polls Telegram API for new messages | Telegram pushes updates to our server |
| Requires a long-running process | Only wakes up when a message arrives |
| Wastes resources when idle | Efficient — zero CPU when idle |
| Cannot run on serverless/free-tier web services | ✅ Perfect for Render free tier |
| Good for local development | ✅ Good for production |

### Webhook Setup

After deployment, a one-time API call registers the webhook:
```
GET https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<RENDER_URL>/webhook
```

### Gunicorn Configuration

| Setting | Value | Reason |
|---------|-------|--------|
| `workers` | 1 | Async event loop must share process with webhook handler |
| `worker_class` | sync | Async is handled by our own thread, not Gunicorn |
| `timeout` | 30s | Attendance scraping can take up to 15-20 seconds |
| `preload_app` | false | Avoid forking issues with threads |

### Keep-Alive Mechanism

Render's free tier sleeps after 15 minutes of inactivity. Solution:
- A daemon thread runs in the background
- Every 10 minutes, it sends an HTTP GET to its own `/ping` endpoint
- Uses `RENDER_EXTERNAL_URL` env var to know its own public URL

---

## 10. Challenges Faced & Solutions

### Challenge 1: Password Encryption (AES-128-CBC)

**Problem**: The ECAP portal encrypts passwords using CryptoJS in the browser before submitting the login form. Sending a plaintext password doesn't work.

**How I Solved It**:
1. Opened browser DevTools → Network tab → observed the login POST
2. Found the encrypted password in `txtPwd2` field
3. Searched the page's JavaScript for CryptoJS usage
4. Extracted the AES key and IV: `8701661282118308`
5. Replicated the encryption in Python using PyCryptodome

### Challenge 2: AjaxPro Protocol

**Problem**: Attendance data is loaded via AJAX, not embedded in the page HTML. The AJAX framework used is **AjaxPro** (legacy ASP.NET), which has a non-standard request/response format.

**How I Solved It**:
1. Analyzed Network tab to find the AJAX endpoint
2. Discovered the `X-AjaxPro-Method` header requirement
3. Reverse-engineered the body format: `key=value\r\nkey=value`
4. Handled multiple response formats (JS string, JSON, wrapped JSON)

### Challenge 3: ASP.NET ViewState

**Problem**: ASP.NET WebForms uses hidden fields (`__VIEWSTATE`, `__EVENTVALIDATION`) that must be submitted with every POST. These are unique per page load.

**How I Solved It**:
- First GET the page → Parse all hidden inputs → Include them in the POST data
- Using `requests.Session()` to maintain cookies across requests

### Challenge 4: Timezone Issues on Cloud Deployment

**Problem**: `datetime.now()` returns UTC on cloud servers, but students expect IST. Today's attendance column lookup failed because dates didn't match.

**How I Solved It**:
```python
ist = timezone(timedelta(hours=5, minutes=30))
today = datetime.now(ist)
```
Used timezone-aware datetime everywhere — no dependency on server timezone.

### Challenge 5: Flask + Async Telegram Bot

**Problem**: `python-telegram-bot` v20 is fully async, but Flask is synchronous. They can't run in the same thread.

**How I Solved It**:
- Created a separate thread with its own `asyncio` event loop
- Flask webhook handler puts updates into an `asyncio.Queue`
- Background thread processes updates asynchronously
- Used `_loop.call_soon_threadsafe()` for thread-safe queue insertion

---

## 11. Key Interview Q&A

### Q: What is this project about?
**A**: It's a Telegram Bot that scrapes attendance data from my college's ECAP portal. Students send their credentials, and the bot logs in on their behalf, extracts attendance percentages, today's P/A status, and calculates how many classes they can skip — all delivered as a formatted Telegram message.

### Q: Why did you choose web scraping instead of using an API?
**A**: The ECAP portal has no public API. It's a legacy ASP.NET WebForms application. The only way to access the data programmatically is to replicate the browser's HTTP requests — which is web scraping.

### Q: How does the password encryption work?
**A**: The portal uses AES-128-CBC encryption on the client side (via CryptoJS). I reverse-engineered the JavaScript to find the key and IV (`8701661282118308`), then replicated the encryption in Python using PyCryptodome. The encrypted password is Base64-encoded before being sent in the POST request.

### Q: How do you handle the AJAX data loading?
**A**: The portal uses AjaxPro, a legacy ASP.NET AJAX framework. I send a POST request to the dynamically discovered Ajax endpoint with a custom `X-AjaxPro-Method` header and a `key=value\r\n` formatted body. The response can come in multiple formats (JS string literal, JSON, wrapped JSON), so I handle all three parsing paths.

### Q: How does the bot handle multiple users simultaneously?
**A**: Each user interaction creates a new `ECAPScraper` instance with its own `requests.Session`. The async event loop processes updates sequentially from a queue, but each scraping operation is independent. Credentials are stored per Telegram user ID in a thread-safe JSON file.

### Q: What happens when the server restarts?
**A**: Credentials are persisted to `user_credentials.json` on disk, so the Refresh button continues to work after restarts. The event loop re-initializes lazily on the first webhook request.

### Q: How did you deploy this for 24/7 availability?
**A**: Deployed on Render's free tier using webhook mode. Telegram pushes updates to our Flask endpoint. A keep-alive thread pings the server every 10 minutes to prevent Render from spinning down the instance. Gunicorn serves the Flask app with 1 worker.

### Q: What are the limitations of this project?
**A**: (1) Credentials stored in plaintext JSON — a production system should use encrypted storage. (2) Dependent on ECAP's HTML structure — if they redesign the portal, the scraper breaks. (3) Render free tier has cold starts of 10-20 seconds. (4) Single worker means requests are processed sequentially.

### Q: What would you do differently if rebuilding this?
**A**: (1) Use a database like SQLite or Redis for credential storage with encryption. (2) Add rate limiting to prevent abuse. (3) Implement proper error retry logic with exponential backoff. (4) Add unit tests with mocked HTML responses. (5) Consider using a headless browser if the portal adds CAPTCHA.

---

## 12. Future Improvements

| Improvement | Benefit |
|-------------|---------|
| **Encrypted credential storage** (SQLite + Fernet) | Better security for stored passwords |
| **Scheduled notifications** | Auto-send attendance updates every morning |
| **Attendance trend graphs** | Visualize attendance over time using matplotlib |
| **Group chat support** | Allow class representatives to check for multiple students |
| **CAPTCHA handling** | Use OCR or headless browser if portal adds CAPTCHA |
| **Rate limiting** | Prevent a single user from making too many requests |
| **Unit tests** | Test parsing logic with saved HTML snapshots |
| **Docker containerization** | More portable deployment |
| **Database migration** | Move from JSON file to PostgreSQL/Redis |
| **Webhook auto-registration** | Set webhook URL automatically on deployment |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────┐
│           ATTENDANCE BOT - QUICK REF            │
├─────────────────────────────────────────────────┤
│ Language:    Python 3.11                        │
│ Framework:   Flask + python-telegram-bot v20    │
│ Scraping:    Requests + BeautifulSoup4          │
│ Encryption:  AES-128-CBC (PyCryptodome)         │
│ Server:      Gunicorn (1 sync worker)           │
│ Deployment:  Render (Free Tier, Webhook Mode)   │
│ Persistence: JSON file (user_credentials.json)  │
│ Timezone:    IST (UTC+5:30) hardcoded           │
│ Keep-Alive:  Self-ping thread every 10 min      │
│ Threading:   Flask main + asyncio background    │
└─────────────────────────────────────────────────┘
```

---

*Last Updated: May 2026*
