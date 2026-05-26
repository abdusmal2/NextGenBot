import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

telegram_app = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is working!")

telegram_app.add_handler(CommandHandler("start", start))


@app.post("/")
def webhook():
    json_data = request.get_json(force=True)

    async def process():
        await telegram_app.initialize()
        update = Update.de_json(json_data, telegram_app.bot)
        await telegram_app.process_update(update)

    asyncio.run(process())

    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
