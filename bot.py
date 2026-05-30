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

# ADD NEW COLUMN IF IT DOESN'T EXIST
try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN receipt_file_id TEXT"
    )
    conn.commit()
except:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid INTEGER DEFAULT 0,
    plan_months INTEGER DEFAULT 0,
    amount INTEGER DEFAULT 0,
    expiry_date TEXT,
    receipt_file_id TEXT
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
                "📅 1 Month",
                callback_data="plan_1"
            )
        ],
        [
            InlineKeyboardButton(
                "📅 2 Months",
                callback_data="plan_2"
            )
        ],
        [
            InlineKeyboardButton(
                "📝 Custom Plan",
                callback_data="custom_plan"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Welcome To NextGen Dub Studio Bot, {user.first_name}!\n\n"
        "🎬 This bot provides access to our VIP community where you can enjoy exclusive dubbed movies, series, and premium content.\n\n"
        "⚠️ If you join the VIP group late and discover that you missed some movies or episodes, please contact our administrators for assistance:\n\n"
        "👤 @Abdusmal\n"
        "👤 @D16graphics\n\n"
        "They will help you with any questions or missing content.\n\n"
        "💎 To enter the VIP group, please select a subscription plan below.",
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

    # 1 MONTH PLAN
    if query.data == "plan_1":

        cursor.execute(
            "UPDATE users SET plan_months=?, amount=? WHERE user_id=?",
            (1, 500, query.from_user.id)
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

        await query.message.reply_text(
            "💎 1 Month VIP Plan\n\n"
            "You are to pay ₦500 to get access.\n\n"
            "Choose a payment method below.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 2 MONTH PLAN
    elif query.data == "plan_2":

        cursor.execute(
            "UPDATE users SET plan_months=?, amount=? WHERE user_id=?",
            (2, 1000, query.from_user.id)
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

        await query.message.reply_text(
            "💎 2 Months VIP Plan\n\n"
            "You are to pay ₦1000 to get access.\n\n"
            "Choose a payment method below.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # CUSTOM PLAN
    elif query.data == "custom_plan":

        await query.message.reply_text(
            "📝 Custom VIP Plan\n\n"
            "Send the number of months you want.\n\n"
            "Examples:\n"
            "3\n"
            "6\n"
            "12"
        )

            # MANUAL PAYMENT
    elif query.data == "manual_payment":

        await query.message.reply_text(
            "💳 Manual Payment\n\n"
            "Bank: Opay\n"
            "Account Name: YOUR NAME\n"
            "Account Number: 1234567890\n\n"
            "After payment, send your receipt screenshot here."
        )

    # ONLINE PAYMENT
    elif query.data == "online_payment":

        await query.message.reply_text(
            "🌐 Online payment system coming soon."
        )

        # CONFIRM PAYMENT
    elif query.data == "confirm_manual_payment":

        user = query.from_user

        cursor.execute(
            "SELECT plan_months, amount FROM users WHERE user_id=?",
            (user.id,)
        )

        result = cursor.fetchone()

        if not result:
            await query.message.reply_text(
                "❌ No plan selected."
            )
            return

        months = result[0]
        amount = result[1]

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

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🚨 New Manual Payment Request\n\n"
                f"Username: @{user.username}\n"
                f"User ID: {user.id}\n\n"
                f"Plan: {months} Month(s)\n"
                f"Amount: ₦{amount}"
            ),
            reply_markup=InlineKeyboardMarkup(admin_keyboard)
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
                0
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

        invite_message = await context.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ Payment Approved!\n\n"
                "Tap the button below to join VIP.\n\n"
                "⚠️ Link usable only once."
            ),
            reply_markup=join_keyboard,
            protect_content=True
        )

        # SAVE MESSAGE ID
        cursor.execute(
            "UPDATE invites SET invite_link_id=? WHERE user_id=?",
            (invite_message.message_id, user_id)
        )

        conn.commit()

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

# RECEIPT UPLOAD
async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not update.message.photo:
        return

    photo = update.message.photo[-1]

    cursor.execute(
        "UPDATE users SET receipt_file_id=? WHERE user_id=?",
        (photo.file_id, user.id)
    )

    conn.commit()

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ I Have Paid",
                callback_data="confirm_manual_payment"
            )
        ]
    ]

    await update.message.reply_text(
        "✅ Receipt received.\n\n"
        "Click the button below to notify admin.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# JOIN DETECTION
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):

    for member in update.message.new_chat_members:

        user_id = member.id

        # FIND USER INVITE
        cursor.execute(
            "SELECT invite_link, invite_link_id FROM invites WHERE user_id=?",
            (user_id,)
        )

        result = cursor.fetchone()

        if result:

            invite_link = result[0]
            message_id = result[1]

            # REVOKE INVITE LINK
            await context.bot.revoke_chat_invite_link(
                chat_id=VIP_GROUP_ID,
                invite_link=invite_link
            )

            # DELETE INVITE MESSAGE
            try:
                await context.bot.delete_message(
                    chat_id=user_id,
                    message_id=message_id
                )
            except:
                pass

            # DELETE SAVED INVITE
            cursor.execute(
                "DELETE FROM invites WHERE user_id=?",
                (user_id,)
            )

            conn.commit()

                        # WELCOME MESSAGE IN VIP GROUP
            import asyncio

            welcome_message = await context.bot.send_message(
                chat_id=VIP_GROUP_ID,
                text=(
                    f"🎉 Welcome to VIP "
                    f"{member.mention_html()} 🔥"
                ),
                parse_mode="HTML"
            )

            # AUTO DELETE AFTER 5 MINUTES
            await asyncio.sleep(300)

            try:
                await context.bot.delete_message(
                    chat_id=VIP_GROUP_ID,
                    message_id=welcome_message.message_id
                )
            except:
                pass


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("groupid", groupid))
telegram_app.add_handler(CallbackQueryHandler(button_handler))

telegram_app.add_handler(
    MessageHandler(
        filters.PHOTO,
        receipt_handler
    )
)

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