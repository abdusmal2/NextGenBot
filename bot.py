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
    CallbackQueryHandler,
    MessageHandler,
    filters
)
import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 7283280924
VIP_GROUP_ID = -1003910567293

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS invites (
    user_id INTEGER,
    invite_link TEXT,
    invite_link_id TEXT
)
""")

conn.commit()

# FASTAPI
app = FastAPI()

telegram_app = Application.builder().token(BOT_TOKEN).build()


# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    # Ignore groups
    if update.effective_chat.type != "private":
        return

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


# GROUP ID COMMAND
async def groupid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    await update.message.reply_text(
        f"Group ID:\n{chat_id}"
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

        admin_keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Approve",
                    callback_data=f"approve_{user.id}"
                ),
                InlineKeyboardButton(
                    "❌ Decline",
                    callback_data=f"decline_{user.id}"
                )
            ]
        ]

        admin_markup = InlineKeyboardMarkup(admin_keyboard)

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🚨 New Manual Payment Request\n\n"
                f"Username: @{user.username}\n"
                f"User ID: {user.id}"
            ),
            reply_markup=admin_markup
        )

        await query.message.reply_text(
            "✅ Payment request sent to admin.\n"
            "Please wait for confirmation."
        )

    # APPROVE USER
    elif query.data.startswith("approve_"):

        user_id = int(query.data.split("_")[1])

        invite = await context.bot.create_chat_invite_link(
            chat_id=VIP_GROUP_ID,
            member_limit=1
        )

        cursor.execute(
            "INSERT INTO invites VALUES (?, ?, ?)",
            (
                user_id,
                invite.invite_link,
                invite.invite_link
            )
        )

        conn.commit()

        join_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "🚀 JOIN VIP",
            url=invite.invite_link
        )
    ]
])

await context.bot.send_message(
    chat_id=user_id,
    text=(
        "✅ Payment Approved!\n\n"
        "Tap the button below to join VIP.\n\n"
        "⚠️ Link usable only once."
    ),
    reply_markup=join_keyboard,
    protect_content=True
)

        await query.message.edit_text(
            "✅ User approved successfully."
        )

    # DECLINE USER
    elif query.data.startswith("decline_"):

        user_id = int(query.data.split("_")[1])

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ Payment not received.\n"
                "Please complete payment and try again or contact admin."
            )
        )

        await query.message.edit_text(
            "❌ Payment declined."
        )


# JOIN DETECTION
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):

    for member in update.message.new_chat_members:

        user_id = member.id

        # FIND USER INVITE
        cursor.execute(
            "SELECT invite_link FROM invites WHERE user_id=?",
            (user_id,)
        )

        result = cursor.fetchone()

        if result:

            invite_link = result[0]

            # REVOKE INVITE LINK
            await context.bot.revoke_chat_invite_link(
                chat_id=VIP_GROUP_ID,
                invite_link=invite_link
            )

            # DELETE SAVED INVITE
            cursor.execute(
                "DELETE FROM invites WHERE user_id=?",
                (user_id,)
            )

            conn.commit()

            # OPTIONAL WELCOME MESSAGE
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ Welcome to VIP."
            )


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("groupid", groupid))
telegram_app.add_handler(CallbackQueryHandler(button_handler))
telegram_app.add_handler(
    MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        new_member
    )
)


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