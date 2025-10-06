import os
import re
import logging
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

from database import SessionLocal
from crud.user import get_user_by_telegram_id
from crud.telegram import create_verification_code, get_verification_code, delete_verification_code
from agent.langchain_agent import process_message

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ============================================================================
# Telegram MarkdownV2 Escaping Functions
# ============================================================================

def escape_markdown_v2(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2.
    Characters that need escaping: _ * [ ] ( ) ~ ` > # + - = | { } . !
    """
    # Escape all special characters except * and _ (used for formatting)
    escape_chars = r'[\\`>#+\-=|{}.!()[\]]'
    return re.sub(escape_chars, r'\\\g<0>', text)

def format_telegram_message(text: str) -> str:
    """
    Format a message for Telegram with proper MarkdownV2 escaping.
    Preserves *bold* and _italic_ formatting while escaping special characters.
    """
    parts = []
    current_pos = 0
    
    # Find all formatting markers: *text* or _text_
    pattern = r'(\*[^*]+\*|_[^_]+_)'
    
    for match in re.finditer(pattern, text):
        # Escape unformatted text before this match
        if match.start() > current_pos:
            unformatted = text[current_pos:match.start()]
            parts.append(escape_markdown_v2(unformatted))
        
        # Handle formatted text (preserve markers, escape content)
        formatted = match.group(0)
        marker = formatted[0]
        content = formatted[1:-1]
        parts.append(f"{marker}{escape_markdown_v2(content)}{marker}")
        
        current_pos = match.end()
    
    # Escape remaining text
    if current_pos < len(text):
        parts.append(escape_markdown_v2(text[current_pos:]))
    
    return ''.join(parts)

# ============================================================================
# Command Handlers
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    logger.info("Received /start command")
    telegram_id = update.message.from_user.id
    db = SessionLocal()
    user = get_user_by_telegram_id(db, telegram_id)
    db.close()

    if user:
        keyboard = [
            [InlineKeyboardButton("Add Items", switch_inline_query_current_chat="I bought ")],
            [InlineKeyboardButton("Check Inventory", switch_inline_query_current_chat="What do I have?")],
            [InlineKeyboardButton("Get a Recipe", switch_inline_query_current_chat="What can I make for dinner?")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"👋 Welcome back, {update.message.from_user.first_name}! I'm Kleio, your personal kitchen assistant.\n\nWhat would you like to do first?",
            reply_markup=reply_markup
        )
    else:
        db = SessionLocal()
        code = create_verification_code(db, telegram_id)
        db.close()
        await update.message.reply_text(
            "🔐 Link Your Account\n\n"
            "To connect this Telegram to Kleio.ai:\n\n"
            "1. Go to: https://kleio.ai/settings\n"
            "2. Click 'Connect Telegram'\n"
            f"3. Enter this code: {code}\n\n"
            "⏰ Code expires in 10 minutes."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    help_text = """
Of course! Here's how I can help you manage your kitchen:

📦 *Inventory Management*
• *Add items:* Just tell me what you bought! Try: "bought 2kg onions, 1L milk, and a loaf of bread"
• *Check stock:* Ask me what you have. Try: "what vegetables do I have?" or "do I have any milk?"

🍳 *Recipes & Cooking*
• *Get ideas:* Ask for a recipe based on your inventory. Try: "what can I make for dinner?"
• *Check a specific recipe:* See if you can make a dish you have in mind. Try: "can I cook paneer butter masala?"

🛒 *Smart Shopping*
• *Generate a list:* I can predict what you need to buy. Try: "what should I buy this week?"

⚙️ *Account*
• /start - Re-links your account if you ever get disconnected.
• /help - Shows this message again.

Just type a message and I'll do my best to understand!
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages."""
    telegram_id = update.message.from_user.id
    message_text = update.message.text
    chat_id = update.message.chat_id

    db = SessionLocal()
    user = get_user_by_telegram_id(db, telegram_id)
    db.close()

    if not user:
        await start(update, context)
        return

    await bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # Get response from agent
        response = await process_message(user.firebase_uid, message_text, str(chat_id))
        
        # ✅ Format the response with proper MarkdownV2 escaping
        formatted_response = format_telegram_message(response)
        
        logger.info(f"📨 Sending formatted response (length: {len(formatted_response)})")
        
        # Send with MarkdownV2 parsing
        await update.message.reply_text(formatted_response, parse_mode='MarkdownV2')
        
    except Exception as e:
        logger.error(f"❌ Error sending message with MarkdownV2: {e}")
        logger.error(f"Raw response: {response}")
        logger.error(f"Formatted response: {formatted_response if 'formatted_response' in locals() else 'N/A'}")
        
        # Fallback: send without formatting
        try:
            await update.message.reply_text(
                "⚠️ Response received, but there was a formatting issue. Here's the plain text:\n\n" + response,
                parse_mode=None
            )
        except Exception as fallback_error:
            logger.error(f"❌ Fallback also failed: {fallback_error}")
            await update.message.reply_text(
                "❌ Sorry, I encountered an error processing your request. Please try again."
            )


def run_bot():
    """Run the Telegram bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Starting Telegram bot...")
    application.run_polling()

if __name__ == "__main__":
    run_bot()