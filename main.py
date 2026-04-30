import os
import time
import threading
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI

# ===== ENV =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
RENDER_URL = os.getenv("RENDER_URL")  # e.g. https://your-app.onrender.com

bot = telebot.TeleBot(BOT_TOKEN)

# ===== AI (DeepSeek via HF router) =====
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

SYSTEM_PROMPT = """
You are a Telegram helper bot.
- Hinglish me short, clear replies
- User ko Download button par guide karo
- Confusion ho to 1-2 steps me samjhao
- Off-topic pe bolo: "Main sirf video/download help ke liye hoon 😊"
"""

# ===== Flask (Webhook) =====
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# ===== Helpers =====
def auto_delete(chat_id, message_ids, delay=300):
    def _del():
        time.sleep(delay)
        for mid in message_ids:
            try:
                bot.delete_message(chat_id, mid)
            except:
                pass
    threading.Thread(target=_del).start()

def ai_reply(user_text):
    try:
        completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V4-Pro:novita",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
        )
        return completion.choices[0].message.content
    except:
        return "⚠️ Thoda issue aaya, baad me try karo."

# ===== Handlers =====
@bot.message_handler(commands=["start"])
def start(msg):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("📥 Download", callback_data="download"),
        InlineKeyboardButton("🎓 Tutorial", callback_data="tutorial")
    )
    m = bot.send_message(
        msg.chat.id,
        "👋 Welcome bhai!\nVideo lene ke liye niche buttons use karo.",
        reply_markup=kb
    )
    auto_delete(msg.chat.id, [m.message_id], 300)

@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    if call.data == "download":
        # 👉 Yahan apna FILE_ID daalna (Telegram se milega)
        FILE_ID = os.getenv("VIDEO_FILE_ID", "")
        if FILE_ID:
            v = bot.send_video(call.message.chat.id, FILE_ID,
                               caption="⚠️ 5 min me message delete ho jayega.")
            auto_delete(call.message.chat.id, [v.message_id], 300)
        else:
            m = bot.send_message(call.message.chat.id, "Video ready nahi hai abhi.")
            auto_delete(call.message.chat.id, [m.message_id], 300)

    elif call.data == "tutorial":
        text = (
            "Steps 👇\n"
            "1) Download button dabao 📥\n"
            "2) Bot se video le lo 🎬\n"
        )
        m = bot.send_message(call.message.chat.id, text)
        auto_delete(call.message.chat.id, [m.message_id], 300)

@bot.message_handler(func=lambda m: True)
def chat(m):
    txt = (m.text or "").lower()
    if any(k in txt for k in ["video", "download", "link"]):
        r = "Download ke liye 📥 button dabao, waha se video mil jayega."
    else:
        r = ai_reply(m.text or "")
    rep = bot.reply_to(m, r)
    auto_delete(m.chat.id, [rep.message_id], 300)

# ===== Run (Webhook set) =====
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=10000)
