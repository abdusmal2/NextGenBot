import os
import sqlite3
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")

# DATABASE
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

# FASTAPI
app = FastAPI()

telegram_app = Application.builder().token(BOT_TOKEN).build()


from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # SAVE USER
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user.id, user.username)
    )

    conn.commit()

    # BUTTONS
    keyboard = [
        [
            InlineKeyboardButton(
                "💳 Manual Payment",
                callback_data="manual_payment"
            )
        ],
        [
            InlineKeyboardButton(
                "🌐 Online Payment",
                callback_data="online_payment"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💎 You are to pay ₦500 to get access 💎",
        reply_markup=reply_markup
    )

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


telegram_app.add_handler(CommandHandler("start", start))


@app.on_event("startup")
async def startup():
    await telegram_app.initialize()


@app.post("/")
async def webhook(request: Request):
    data = await request.json()

    update = Update.de_json(data, telegram_app.bot)

    await telegram_app.process_update(update)

    return {"ok": True}


@app.get("/")
async def home():
    return {"status": "running"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)