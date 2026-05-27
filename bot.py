import os
import sqlite3
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

BOT_TOKEN = os.getenv("BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_URL")

# DATABASE SETUP
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid INTEGER DEFAULT 0
)
""")

conn.commit()

# BOT
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # SAVE USER
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user.id, user.username)
    )
    conn.commit()

    await update.message.reply_text(
        "Welcome!\n\n"
        "Your account has been registered.\n"
        "Please make payment to access the VIP group."
    )

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=RENDER_URL,
        url_path="webhook",
    )