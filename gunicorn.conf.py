"""
Gunicorn configuration for Telegram Bot with async event loop.

CRITICAL: This bot uses a custom threading + async queue architecture.
It MUST run with exactly 1 worker to ensure the event loop thread
runs in the same process that handles webhook requests.
"""

import os

# Bind to the port provided by Render
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# CRITICAL: Use exactly 1 worker
# The bot's event loop thread must run in the same process as the webhook handler
workers = 1

# Worker class - sync is fine since we handle async in a separate thread
worker_class = "sync"

# Timeout for requests (30 seconds should be enough for attendance scraping)
timeout = 30

# Keep alive connections
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Preload app to initialize the event loop before forking
preload_app = False

# Graceful timeout for worker shutdown
graceful_timeout = 30

# Max requests per worker before restart (helps prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50
