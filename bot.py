import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

telegram_app = Application.builder().token(BOT_TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is working!")


telegram_app.add_handler(CommandHandler("start", start))


@app.before_request
def initialize():
    import asyncio
    try:
        asyncio.get_event_loop().run_until_complete(telegram_app.initialize())
    except:
        pass


@app.route("/", methods=["POST"])
def webhook():
    import asyncio

    update = Update.de_json(request.get_json(force=True), telegram_app.bot)

    asyncio.get_event_loop().run_until_complete(
        telegram_app.process_update(update)
    )

    return "ok"


@app.route("/", methods=["GET"])
def home():
    return "Bot running"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)