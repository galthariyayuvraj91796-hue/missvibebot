import os
import time
import threading
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI

# ================= ENV VARIABLES =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
RENDER_URL = os.getenv("RENDER_URL")
VIDEO_FILE_ID = os.getenv("VIDEO_FILE_ID")

# ================= TELEGRAM BOT =================
bot = telebot.TeleBot(BOT_TOKEN)

# ================= AI CLIENT =================
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# ================= FLASK =================
app = Flask(__name__)

# ================= PROMPT =================
SYSTEM_PROMPT = """
You are a Telegram bot that helps users get videos from a channel.

- Always reply in Hinglish
- Keep replies short
- Focus only on video/download help
- If user says hi → "👋 Welcome bhai, Download button dabao 📥"
- If user asks for video → tell them to click Download button
- If unrelated question → "Main sirf video aur download help ke liye hoon 😊"
"""

# ================= AI FUNCTION =================
def ai_reply(user_text):
    try:
        res = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V4-Pro:novita",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
        )
        return res.choices[0].message.content
    except:
        return "⚠️ Thoda issue aaya, baad me try karo."

# ================= AUTO DELETE =================
def auto_delete(chat_id, message_ids):
    def delete():
        time.sleep(300)  # 5 min
        for msg_id in message_ids:
            try:
                bot.delete_message(chat_id, msg_id)
            except:
                pass
    threading.Thread(target=delete).start()

# ================= START COMMAND =================
@bot.message_handler(commands=['start'])
def start(msg):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📥 Download", callback_data="download"),
        InlineKeyboardButton("🎓 Tutorial", callback_data="tutorial")
    )

    sent = bot.send_message(
        msg.chat.id,
        "👋 Welcome bhai!\nVideo lene ke liye niche button dabao 📥",
        reply_markup=markup
    )

    auto_delete(msg.chat.id, [sent.message_id])

# ================= BUTTON HANDLER =================
@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):

    if call.data == "download":
        if VIDEO_FILE_ID:
            video_msg = bot.send_video(
                call.message.chat.id,
                VIDEO_FILE_ID,
                caption="⚠️ Ye video 5 minute me delete ho jayega!"
            )

            auto_delete(call.message.chat.id, [video_msg.message_id])

        else:
            msg = bot.send_message(call.message.chat.id, "Video abhi available nahi hai.")
            auto_delete(call.message.chat.id, [msg.message_id])

    elif call.data == "tutorial":
        msg = bot.send_message(
            call.message.chat.id,
            "🎓 Steps:\n1. Download button dabao\n2. Video mil jayega 🎬"
        )
        auto_delete(call.message.chat.id, [msg.message_id])

# ================= CHAT HANDLER =================
@bot.message_handler(func=lambda message: True)
def chat(message):
    text = message.text.lower()

    if "video" in text or "download" in text:
        reply = "📥 Video ke liye Download button dabao."
    else:
        reply = ai_reply(text)

    sent = bot.reply_to(message, reply)
    auto_delete(message.chat.id, [sent.message_id])

# ================= WEBHOOK =================
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def home():
    return "Bot Running!"

# ================= START =================
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=10000)
