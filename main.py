import os
import sqlite3
import json
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DB_PATH = 'alerts.db'

# YOUR ACTION REQUIRED: Replace with your actual HTTPS link
MINI_APP_URL = "https://your-username.github.io/your-repo/" 

# --- DATABASE SETUP ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
                     user_id INTEGER PRIMARY KEY, 
                     coins INTEGER DEFAULT 0)''')
    print("📁 Database Ready: NitroTrade Records Active.")

# --- MARKET LOGIC ---
def get_btc_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5)
        return r.json()['bitcoin']['usd']
    except:
        return None

# --- TELEGRAM HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    
    keyboard = [
        [KeyboardButton("💰 My Wallet"), KeyboardButton("🏎️ Nitro Boost")],
        [KeyboardButton("📈 Market Prices")]
    ]
    await update.message.reply_text(
        "🏎️ **Sovereign Core Online**\nWallet linked. Ready for extraction.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode='Markdown'
    )

async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes the signal sent from index.html after the video ends"""
    try:
        raw_data = update.effective_message.web_app_data.data
        payload = json.loads(raw_data)

        if payload.get("action") == "reward_user":
            user_id = update.effective_user.id
            amount = payload.get("amount", 50)
            
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
                
            await update.message.reply_text(
                f"⚡ **Nitro Boost Successful!**\n+{amount} coins siphoned to your wallet."
            )
    except Exception as e:
        print(f"Siphon Error: {e}")

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "💰 My Wallet":
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,)).fetchone()
            balance = row[0] if row else 0
        await update.message.reply_text(f"💳 **Current Assets:** {balance} Coins")

    elif text == "📈 Market Prices":
        price = get_btc_price()
        await update.message.reply_text(f"📊 **BTC Value:** ${price:,}" if price else "⚠️ Feed offline.")

    elif text == "🏎️ Nitro Boost":
        await update.message.reply_text(
            "🚀 **Extraction Window Open**\nFinish the video transmission to secure 50 coins.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📺 Start Extraction", web_app=WebAppInfo(url=MINI_APP_URL))]
            ])
        )

# --- EXECUTION ENGINE ---
if __name__ == '__main__':
    init_db()
    if not TOKEN:
        print("❌ CRITICAL: TELEGRAM_BOT_TOKEN not found.")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Mapping Handlers
        app.add_handler(CommandHandler('start', start))
        app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_messages))
        
        print(">> Core Listening: Waiting for user activity...")
        app.run_polling()