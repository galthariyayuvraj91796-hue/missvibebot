import os
import telebot
from flask import Flask, request
from openai import OpenAI

# ── Env Variables ──────────────────────────────────────────────
BOT_TOKEN  = os.environ["BOT_TOKEN"]
HF_TOKEN   = os.environ["HF_TOKEN"]
RENDER_URL = os.environ["RENDER_URL"]   # e.g. https://your-app.onrender.com

# ── Clients ────────────────────────────────────────────────────
bot = telebot.TeleBot(BOT_TOKEN)

ai_client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

app = Flask(__name__)

# ── System Prompt ──────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a Telegram bot that helps users get videos from a channel.

Language & Style:
- Always reply in Hinglish (Hindi + English mix)
- Keep replies very short and clear (2-3 lines max)
- Use simple words and helpful emojis

Your Rules:
1. If user says hi/hello/hey → reply exactly:
   "👋 Welcome bhai, video lene ke liye Download button dabao 📥"

2. If user asks for video, download, link, or file → tell them to click "Download" button and give 1-2 simple steps.

3. If user is confused or asks how to use → give short step-by-step instructions.

4. If user asks anything unrelated to videos/downloads → reply exactly:
   "Main sirf video aur download help ke liye hoon 😊"

5. Never give long answers. Stay focused on helping with video downloads only.

Tone: Short, direct, friendly, helpful.
"""

# ── AI Reply Helper ────────────────────────────────────────────
def get_ai_reply(user_message: str) -> str:
    try:
        response = ai_client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V4-Pro:novita",
            max_tokens=200,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return "Kuch gadbad ho gayi 😅 Thodi der baad try karo."

# ── Bot Handlers ───────────────────────────────────────────────
@bot.message_handler(commands=["start", "help"])
def handle_start(message):
    bot.reply_to(
        message,
        "👋 Welcome bhai, video lene ke liye Download button dabao 📥"
    )

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    user_text = message.text or ""
    print(f"User [{message.from_user.id}]: {user_text}")

    reply = get_ai_reply(user_text)
    print(f"Bot reply: {reply}")

    bot.reply_to(message, reply)

# ── Flask Webhook Routes ───────────────────────────────────────
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running! 🤖", 200

# ── Set Webhook & Run ──────────────────────────────────────────
def set_webhook():
    webhook_url = f"{RENDER_URL}/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook set: {webhook_url}")

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=10000)
