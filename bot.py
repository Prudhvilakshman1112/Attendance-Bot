import logging
import os
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import config
from scraper import ECAPScraper
from attendance_utils import parse_attendance, format_message

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize Telegram bot application globally
ptb_app = Application.builder().token(config.BOT_TOKEN).build()

# Track initialization status
_initialized = False

async def initialize_bot():
    """Initialize the bot application if not already initialized."""
    global _initialized
    if not _initialized:
        await ptb_app.initialize()
        await ptb_app.start()
        _initialized = True
        logger.info("Bot application initialized successfully")

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
        
        # Store credentials for this user (for refresh functionality)
        # Use username as key to support multiple users
        if 'users' not in context.user_data:
            context.user_data['users'] = {}
        
        context.user_data['users'][username] = password
        
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
    
    # Check if we have stored credentials for this user
    if 'users' not in context.user_data or username not in context.user_data['users']:
        await query.edit_message_text(
            text=f"❌ Session expired for {username}.\n\nPlease send credentials again: `{username} password`",
            parse_mode='Markdown'
        )
        return
    
    password = context.user_data['users'][username]
    
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
    """Clear all stored credentials."""
    if 'users' in context.user_data:
        count = len(context.user_data['users'])
        context.user_data['users'] = {}
        await update.message.reply_text(f"✅ Cleared {count} stored session(s).")
    else:
        await update.message.reply_text("No active sessions to clear.")

# Register handlers globally
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CommandHandler("cancel", cancel))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_credentials))
ptb_app.add_handler(CallbackQueryHandler(refresh_button_handler, pattern="^refresh_"))

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram updates via webhook."""
    if request.method == "POST":
        # Initialize bot if needed
        asyncio.run(initialize_bot())
        # Parse the incoming update
        update = Update.de_json(request.get_json(force=True), ptb_app.bot)
        # Process the update asynchronously
        asyncio.run(ptb_app.process_update(update))
    return "ok", 200

@app.route('/')
def index():
    """Health check endpoint for Render."""
    return "Attendance Bot is Running ✅", 200

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
