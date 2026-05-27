import os
import sqlite3
from fastapi import FastAPI, Request
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler
)
import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 7283280924

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


# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
async def groupid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    await update.message.reply_text(
        f"Group ID:\n{chat_id}"
    )

    user = update.effective_user

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user.id, user.username)
    )

    conn.commit()

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


# BUTTON HANDLER
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    # MANUAL PAYMENT
    if query.data == "manual_payment":

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ I Have Paid",
                    callback_data="confirm_manual_payment"
                )
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            "💳 Manual Payment\n\n"
            "Bank: Opay\n"
            "Account Name: YOUR NAME\n"
            "Account Number: 1234567890\n\n"
            "After payment click the button below.",
            reply_markup=reply_markup
        )

    # ONLINE PAYMENT
    elif query.data == "online_payment":

        await query.message.reply_text(
            "🌐 Online payment system coming soon."
        )

    # CONFIRM PAYMENT
    elif query.data == "confirm_manual_payment":

        user = query.from_user

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🚨 New Manual Payment Request\n\n"
                f"Username: @{user.username}\n"
                f"User ID: {user.id}"
            )
        )

        await query.message.reply_text(
            "✅ Payment request sent to admin.\n"
            "Please wait for confirmation."
        )


telegram_app.add_handler(CommandHandler("start", start))

telegram_app.add_handler(
    CallbackQueryHandler(button_handler)
)

telegram_app.add_handler(CommandHandler("groupid", groupid))

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