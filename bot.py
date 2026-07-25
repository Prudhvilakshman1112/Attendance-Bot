import logging
import os
import asyncio
import threading
import json
import time
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import config
from scraper import ECAPScraper
from attendance_utils import parse_attendance, format_message

# ---------------------------------------------------------------------------
# Persistent credential store
# Credentials are saved to a JSON file so they survive process restarts.
# ---------------------------------------------------------------------------
CREDS_FILE = os.path.join(os.path.dirname(__file__), "user_credentials.json")
_creds_lock = threading.Lock()

def _load_creds() -> dict:
    """Load all credentials from disk."""
    try:
        with open(CREDS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _save_creds(data: dict):
    """Persist all credentials to disk."""
    with open(CREDS_FILE, "w") as f:
        json.dump(data, f)

def store_user_cred(telegram_user_id: int, username: str, password: str):
    """Store a credential entry for a Telegram user."""
    with _creds_lock:
        data = _load_creds()
        uid = str(telegram_user_id)
        if uid not in data:
            data[uid] = {}
        data[uid][username] = password
        _save_creds(data)

def get_user_cred(telegram_user_id: int, username: str):
    """Return stored password or None."""
    with _creds_lock:
        data = _load_creds()
        return data.get(str(telegram_user_id), {}).get(username)

def get_all_user_creds(telegram_user_id: int) -> dict:
    """Return all stored credentials for a Telegram user."""
    with _creds_lock:
        data = _load_creds()
        return data.get(str(telegram_user_id), {})

def clear_user_creds(telegram_user_id: int) -> int:
    """Remove all credentials for a Telegram user and return how many were removed."""
    with _creds_lock:
        data = _load_creds()
        uid = str(telegram_user_id)
        count = len(data.pop(uid, {}))
        _save_creds(data)
        return count

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize Telegram bot application globally (with error handling for missing/invalid token)
ptb_app = None
if config.BOT_TOKEN:
    try:
        ptb_app = Application.builder().token(config.BOT_TOKEN).build()
        logger.info("Telegram Bot Application built successfully")
    except Exception as err:
        logger.error(f"Failed to build Telegram Bot Application with provided BOT_TOKEN: {err}")
else:
    logger.error("CRITICAL: BOT_TOKEN environment variable is not set or empty!")

# Queue for updates and event loop management (will be created in event loop thread)
update_queue = None
_loop = None
_loop_thread = None


def start_event_loop():
    """Start the event loop in a separate thread."""
    global _loop, _loop_thread, update_queue
    
    async def process_updates():
        """Process updates from the queue."""
        await ptb_app.initialize()
        await ptb_app.start()
        logger.info("Bot initialized and ready")
        
        while True:
            try:
                update = await update_queue.get()
                if update is None:
                    break
                await ptb_app.process_update(update)
            except Exception as e:
                logger.error(f"Error processing update: {e}", exc_info=True)
    
    def run_loop():
        global _loop, update_queue
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
        update_queue = asyncio.Queue()
        _loop.run_until_complete(process_updates())
    
    _loop_thread = threading.Thread(target=run_loop, daemon=True)
    _loop_thread.start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    welcome_message = (
        f"👋 Hi {user.mention_html()}!\n\n"
        "🎓 <b>Welcome to Vignan ECAP Attendance Bot!</b>\n\n"
        "I can help you quickly check your attendance from the Vignan College ECAP portal. "
        "Get instant updates on your attendance percentage, subject-wise details, and today's attendance!\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>📖 HOW TO USE:</b>\n\n"
        "1️⃣ Send your ECAP credentials in this format:\n"
        "   <code>rollnumber password</code>\n\n"
        "2️⃣ Example:\n"
        "   <code>23L31A4391 mypassword</code>\n\n"
        "3️⃣ Wait for the bot to fetch your attendance data\n\n"
        "4️⃣ Use the 🔄 <b>Refresh</b> button to update your data anytime\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🔒 SECURITY NOTE:</b>\n"
        "• Your credentials are automatically deleted after sending\n"
        "• Credentials are stored temporarily only for the refresh feature\n"
        "• Use /cancel to clear all stored sessions\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>📋 AVAILABLE COMMANDS:</b>\n"
        "/start - Show this welcome message\n"
        "/cancel - Clear all stored sessions\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>✨ FEATURES:</b>\n"
        "✅ Subject-wise attendance percentage\n"
        "✅ Today's attendance status\n"
        "✅ Skippable hours calculation (to maintain 75%)\n"
        "✅ Quick refresh button for real-time updates\n"
        "✅ Support for multiple accounts\n\n"
        "💡 <i>Tip: You can check multiple accounts by sending different credentials!</i>\n\n"
        "Ready to get started? Just send your credentials! 🚀"
    )
    await update.message.reply_html(welcome_message)

async def handle_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle credentials sent as a message (username password)."""
    text = update.message.text.strip()
    parts = text.split(' ', 1)
    
    # Check if it's in the format: username password
    if len(parts) < 2:
        return  # Not credentials, ignore
    
    username = parts[0]
    password = parts[1]
    
    # Validate username format (basic check)
    if not username.isalnum() or len(username) < 5:
        return  # Not a valid username format, ignore
    
    # Delete the message with credentials for security
    try:
        await update.message.delete()
    except:
        pass
    
    # Process the credentials
    status_message = await update.message.reply_text("🔐 Credentials received. Logging in...")
    
    try:
        scraper = ECAPScraper()
        
        # Login
        await status_message.edit_text(f"🔐 Logging in as {username}...")
        success, msg = scraper.login(username, password)
        
        if not success:
            await status_message.edit_text(f"❌ Login Failed: {msg}\n\nPlease check your credentials and try again.")
            return
        
        # Fetch cumulative attendance
        await status_message.edit_text("📊 Fetching attendance details...")
        html_content = scraper.get_attendance()
        
        if not html_content:
            await status_message.edit_text("❌ Failed to retrieve attendance page.")
            return
        
        # Parse attendance
        await status_message.edit_text("⚙️ Parsing data...")
        data = parse_attendance(html_content)
        
        if not data:
            await status_message.edit_text("❌ Failed to parse attendance data.")
            return
        
        # Fetch today's attendance
        todays_attendance = scraper.get_todays_attendance()
        
        # Format message
        message = format_message(data, username, todays_attendance)
        
        # Persist credentials to disk so they survive restarts
        store_user_cred(update.effective_user.id, username, password)
        
        # Create refresh button with username in callback data
        keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{username}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await status_message.edit_text(message, reply_markup=reply_markup)
        
    except Exception as e:
        await status_message.edit_text(f"❌ An error occurred: {str(e)}")
        logger.error(f"Error processing credentials for {username}: {e}", exc_info=True)

async def refresh_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle refresh button clicks."""
    query = update.callback_query
    await query.answer()
    
    # Extract username from callback data
    callback_data = query.data
    if not callback_data.startswith("refresh_"):
        return
    
    username = callback_data.replace("refresh_", "")
    
    # Check if we have stored credentials for this user (loaded from disk)
    password = get_user_cred(query.from_user.id, username)
    if not password:
        await query.edit_message_text(
            text=f"❌ Session expired for {username}.\n\nPlease send credentials again: `{username} password`",
            parse_mode='Markdown'
        )
        return
    
    # Update status
    await query.edit_message_text(f"🔄 Refreshing data for {username}...")
    
    try:
        scraper = ECAPScraper()
        
        # Login
        success, msg = scraper.login(username, password)
        
        if not success:
            await query.edit_message_text(f"❌ Login Failed: {msg}\n\nPlease send credentials again.")
            return
        
        # Fetch attendance
        html_content = scraper.get_attendance()
        
        if not html_content:
            await query.edit_message_text("❌ Failed to retrieve attendance page.")
            return
        
        # Parse attendance
        data = parse_attendance(html_content)
        
        if not data:
            await query.edit_message_text("❌ Failed to parse attendance data.")
            return
        
        # Fetch today's attendance
        todays_attendance = scraper.get_todays_attendance()
        
        # Format message
        message = format_message(data, username, todays_attendance)
        
        # Create refresh button
        keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{username}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup)
        
    except Exception as e:
        await query.edit_message_text(f"❌ An error occurred: {str(e)}")
        logger.error(f"Error during refresh for {username}: {e}", exc_info=True)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear all stored credentials from disk."""
    count = clear_user_creds(update.effective_user.id)
    if count:
        await update.message.reply_text(f"✅ Cleared {count} stored session(s).")
    else:
        await update.message.reply_text("No active sessions to clear.")

# Register handlers globally
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CommandHandler("cancel", cancel))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_credentials))
ptb_app.add_handler(CallbackQueryHandler(refresh_button_handler, pattern="^refresh_"))

# Lock for thread-safe initialization
_init_lock = threading.Lock()
_initialized = False

def ensure_event_loop_started():
    """Ensure the event loop is started (called lazily on first request)."""
    global _initialized
    if not _initialized:
        with _init_lock:
            if not _initialized:
                logger.info("Starting event loop thread...")
                start_event_loop()
                # Wait for queue to be ready
                import time
                timeout = 10
                start_time = time.time()
                while update_queue is None and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if update_queue is None:
                    logger.error("CRITICAL: Event loop failed to initialize within timeout!")
                else:
                    logger.info("Event loop initialized successfully")
                    
                _initialized = True
                logger.info("Bot ready to process updates")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram updates via webhook."""
    if ptb_app is None:
        logger.error("Webhook called but ptb_app is None (BOT_TOKEN missing or invalid)")
        return "Bot Token Not Configured", 500

    ensure_event_loop_started()
    
    if request.method == "POST":
        try:
            if update_queue is None:
                logger.error("Update queue not initialized - event loop may have failed to start")
                return "Queue not ready", 503
            
            json_data = request.get_json(force=True)
            logger.info(f"Received webhook update: {json_data.get('update_id', 'unknown')}")
            update = Update.de_json(json_data, ptb_app.bot)
            _loop.call_soon_threadsafe(update_queue.put_nowait, update)
            logger.info("Update queued successfully")
        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
            return "Error processing update", 500
    return "ok", 200

@app.route('/')
def index():
    """Health check endpoint for Render."""
    if ptb_app is None:
        return "⚠️ Attendance Bot is Running, but BOT_TOKEN environment variable is NOT set in Render! Please set BOT_TOKEN in Render Environment variables.", 500
    return "Attendance Bot is Running ✅", 200


@app.route('/ping')
def ping():
    """Lightweight keep-alive ping endpoint."""
    return "pong", 200

# ---------------------------------------------------------------------------
# Self-ping keep-alive thread
# Render free-tier spins down services after ~15 min of inactivity.
# This thread pings the service every 10 minutes to keep it awake.
# ---------------------------------------------------------------------------
def _keep_alive():
    """Background thread that pings this service every 10 minutes."""
    # Wait for the app to fully start before pinging
    time.sleep(30)
    render_url = os.getenv("RENDER_EXTERNAL_URL", "")
    if not render_url:
        logger.info("RENDER_EXTERNAL_URL not set — keep-alive disabled")
        return
    ping_url = render_url.rstrip("/") + "/ping"
    logger.info(f"Keep-alive thread started, will ping {ping_url} every 10 min")
    while True:
        try:
            import urllib.request
            urllib.request.urlopen(ping_url, timeout=10)
            logger.info("Keep-alive ping sent")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        time.sleep(600)  # 10 minutes

_keep_alive_thread = threading.Thread(target=_keep_alive, daemon=True)
_keep_alive_thread.start()

def main() -> None:
    """Run the bot in polling mode (for local testing only)."""
    logger.info("Starting bot in POLLING mode (local testing)")
    ptb_app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Check if we should use polling mode (for local testing)
    USE_POLLING = os.getenv("USE_POLLING", "false").lower() == "true"
    
    if USE_POLLING:
        # Local testing with polling
        main()
    else:
        # Production mode with Flask/webhook
        # Render will use Gunicorn to run the Flask app
        port = int(os.getenv("PORT", 8000))
        logger.info(f"Starting Flask app on port {port}")
        app.run(host="0.0.0.0", port=port)
