import time
import re
import datetime
import threading
import json
import requests
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "PA OF REHANNN 24/7 Live!"

# Apna naya bot token yahan daalein
BOT_TOKEN = "8809883023:AAHFjmVVAFdo75u1MCgRMkcgVymJmuXlGR8"
GEMINI_KEY = "AQ.Ab8RN6I1k5p6rbrIcRXEnZxa6u9uWlghABXNj5Z2lhKmNvIBbw"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

SYSTEM_PROMPT = """
You are acting as the AI Personal Assistant (PA) of Rehan.
Identity Rules (STRICT):
- When asked 'who are you', 'tum kaun ho', or about identity: "Main Rehan ka Personal Assistant (PA) hoon 😎🤝".

Tone & Personality:
- Chat like a real person in natural, chill, friendly Hinglish (dost style).
- Har message ka polite aur dynamic reply do.
- Emojis ka khoob use karo (🔥, 😂, 🤝, 💯, ✨, 🙌).
- Crisp 1-2 sentence replies, no long corporate lectures.
"""

processed_msg_ids = set()
rehan_last_reply_time = {}
chat_sleep_until = {}
chat_history = {}
scheduled_tasks = []
global_bot_muted = False

def is_night_time():
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    hour = ist_now.hour
    return hour >= 23 or hour < 7

def get_admin_keyboard():
    # 4 Main colorful control buttons
    keyboard = {
        "keyboard": [
            [{"text": "⚡ Wake Up"}, {"text": "💤 Sleep 30m"}],
            [{"text": "📊 Bot Status"}, {"text": "📜 All Commands"}]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }
    return json.dumps(keyboard)

def send_reply(chat_id, text, connection_id=None, reply_markup=None):
    try:
        payload = {"chat_id": chat_id, "text": text}
        if connection_id:
            payload["business_connection_id"] = connection_id
        if reply_markup:
            payload["reply_markup"] = reply_markup
        requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")

def get_ai_reply(chat_id, user_text):
    try:
        history = chat_history.get(chat_id, [])
        contents = []
        for h in history[-5:]:
            contents.append({
                "role": "user" if h["from"] == "user" else "model",
                "parts": [{"text": h["text"]}]
            })
        contents.append({
            "role": "user",
            "parts": [{"text": user_text}]
        })

        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": contents
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_KEY
        }
        res = requests.post(f"{GEMINI_URL}?key={GEMINI_KEY}", json=payload, headers=headers, timeout=12)
        data = res.json()
        candidates = data.get("candidates", [])
        if candidates:
            reply = candidates[0]["content"]["parts"][0]["text"].strip()
            if chat_id not in chat_history:
                chat_history[chat_id] = []
            chat_history[chat_id].append({"from": "user", "text": user_text})
            chat_history[chat_id].append({"from": "model", "text": reply})
            if len(chat_history[chat_id]) > 10:
                chat_history[chat_id] = chat_history[chat_id][-10:]
            return reply
    except Exception as e:
        print("API Error:", e)
    return None

def handle_admin_command(text, chat_id, conn_id):
    global global_bot_muted
    cmd = text.strip()

    if cmd.lower() in ["/start", "📜 all commands", "/all"]:
        help_text = (
            "👑 *PA OF REHAN - CONTROL PANEL* 👑\n\n"
            "Neeche diye buttons se control karein ya ye commands type karein:\n\n"
            "🔹 `⚡ Wake Up` (/wake) : Bot ko turant active karne ke liye\n"
            "🔹 `💤 Sleep 30m` : Bot ko 30 min ke liye sulane ke liye\n"
            "🔹 `/sleep <min>` : Jitne minute chahein utna sleep set karein\n"
            "🔹 `📊 Bot Status` (/status) : Current status dekhne ke liye\n"
            "🔹 `/silent on` / `/silent off` : Poora bot mute/unmute karne ke liye\n"
            "🔹 `/sdl <chat_id> 15:30 <msg>` : Scheduled message ke liye"
        )
        send_reply(chat_id, help_text, conn_id, reply_markup=get_admin_keyboard())
        return True

    if cmd in ["💤 Sleep 30m", "/sleep30min", "/sleep 30"]:
        chat_sleep_until[chat_id] = time.time() + (30 * 60)
        send_reply(chat_id, "😴 Done! Bot ab agle 30 minute tak koi reply nahi dega.", conn_id)
        return True

    sleep_match = re.match(r"^/sleep\s*(\d+)(?:min|m)?$", cmd.lower())
    if sleep_match:
        minutes = int(sleep_match.group(1))
        chat_sleep_until[chat_id] = time.time() + (minutes * 60)
        send_reply(chat_id, f"😴 Bot ab is chat me agle {minutes} minute tak sleep mode me rahega.", conn_id)
        return True

    if cmd in ["⚡ Wake Up", "/wake"]:
        if chat_id in chat_sleep_until:
            del chat_sleep_until[chat_id]
        send_reply(chat_id, "⚡ Bot full active ho gaya hai!", conn_id)
        return True

    if cmd in ["📊 Bot Status", "/status"]:
        now = time.time()
        is_sleeping = chat_sleep_until.get(chat_id, 0) > now
        rem = int((chat_sleep_until.get(chat_id, 0) - now) / 60) if is_sleeping else 0
        status_msg = f"📊 *Current Status:*\n- Sleep Mode: {'Haan (' + str(rem) + 'm left)' if is_sleeping else 'Active'}\n- Global Mute: {'ON' if global_bot_muted else 'OFF'}"
        send_reply(chat_id, status_msg, conn_id)
        return True

    if cmd.lower() == "/silent on":
        global_bot_muted = True
        send_reply(chat_id, "🔇 Global Silent Mode ON!", conn_id)
        return True

    if cmd.lower() == "/silent off":
        global_bot_muted = False
        send_reply(chat_id, "🔊 Global Silent Mode OFF!", conn_id)
        return True

    if cmd.lower().startswith("/sdl "):
        parts = cmd.split(" ", 3)
        if len(parts) >= 4:
            scheduled_tasks.append({
                "target_chat": parts[1],
                "time_str": parts[2],
                "msg": parts[3],
                "conn_id": conn_id
            })
            send_reply(chat_id, f"⏰ Scheduled at {parts[2]} for `{parts[1]}`!", conn_id)
            return True
        else:
            send_reply(chat_id, "❌ Format: `/sdl <chat_id> 15:30 Message`", conn_id)
            return True

    return False

def scheduler_worker():
    while True:
        try:
            utc_now = datetime.datetime.utcnow()
            ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
            current_time_str = ist_now.strftime("%H:%M")

            for task in list(scheduled_tasks):
                if task["time_str"] == current_time_str:
                    send_reply(task["target_chat"], task["msg"], task.get("conn_id"))
                    scheduled_tasks.remove(task)
            time.sleep(30)
        except Exception:
            time.sleep(30)

def handle_delayed_response(chat_id, conn_id, user_text, msg_timestamp):
    time.sleep(25)

    last_rehan = rehan_last_reply_time.get(chat_id, 0)
    if last_rehan > msg_timestamp:
        return

    if time.time() < chat_sleep_until.get(chat_id, 0) or global_bot_muted:
        return

    if is_night_time():
        send_reply(chat_id, "Rehan bhai abhi so rahe hain 😴, subah baat karenge! Main unka PA hoon 😎🤝", conn_id)
        return

    if (time.time() - last_rehan) < 600 and conn_id:
        busy_msg = "Abhi Rehan kuch kaam kar rahe hain, thode der baad msg karna. Main unka Personal Assistant hoon! 😎🤝"
        send_reply(chat_id, busy_msg, conn_id)
        return

    ai_reply = get_ai_reply(chat_id, user_text)
    if not ai_reply:
        ai_reply = "Abhi Rehan kuch kaam kar rahe hain, thode der baad msg karna. Main unka Personal Assistant hoon! 😎🤝"

    send_reply(chat_id, ai_reply, conn_id)

def run_bot():
    print("🔥 PA OF REHAN Multi-Mode Active...")
    offset = None

    st = threading.Thread(target=scheduler_worker)
    st.daemon = True
    st.start()

    while True:
        try:
            params = {"timeout": 20, "allowed_updates": ["message", "business_message"]}
            if offset:
                params["offset"] = offset

            resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=30).json()

            for update in resp.get("result", []):
                offset = update["update_id"] + 1

                # 1. Direct Private Message
                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")

                    if handle_admin_command(text, chat_id, None):
                        continue

                    # Direct private chat me AI instant reply
                    ai_reply = get_ai_reply(chat_id, text)
                    if ai_reply:
                        send_reply(chat_id, ai_reply)

                # 2. Business Message
                elif "business_message" in update:
                    b_msg = update["business_message"]
                    msg_id = b_msg.get("message_id")

                    if msg_id in processed_msg_ids:
                        continue
                    processed_msg_ids.add(msg_id)

                    chat_id = b_msg["chat"]["id"]
                    conn_id = b_msg.get("business_connection_id")
                    user_text = b_msg.get("text", "")
                    is_outbound = b_msg.get("is_outgoing", False)

                    if is_outbound:
                        rehan_last_reply_time[chat_id] = time.time()
                        handle_admin_command(user_text, chat_id, conn_id)
                        continue

                    if not user_text or time.time() < chat_sleep_until.get(chat_id, 0):
                        continue

                    t = threading.Thread(
                        target=handle_delayed_response,
                        args=(chat_id, conn_id, user_text, time.time())
                    )
                    t.daemon = True
                    t.start()

        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=10000)
        
