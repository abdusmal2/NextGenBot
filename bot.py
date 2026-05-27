import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = FastAPI()

telegram_app = Application.builder().token(BOT_TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Muna kan aikine, aɗan jira!")


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