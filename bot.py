import time
import re
import datetime
import threading
import requests
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "PA OF REHANNN 24/7 Super-Bot Live!"

BOT_TOKEN = "8809883023:AAHg2I43xWb-seY78bMiCOc5AA7se8Y6rY8"
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
rehan_last_reply_time = {}   # Rehan's active chat tracker
chat_sleep_until = {}        # Per-chat sleep timer
chat_history = {}            # Smart memory (last 5 messages)
scheduled_tasks = []         # Scheduled message queue
global_bot_muted = False

def is_night_time():
    # India Time (UTC + 5:30)
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    hour = ist_now.hour
    return hour >= 23 or hour < 7

def get_ai_reply(chat_id, user_text):
    try:
        # History setup
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
            # Save to history
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

def send_reply(chat_id, text, connection_id=None):
    try:
        payload = {"chat_id": chat_id, "text": text}
        if connection_id:
            payload["business_connection_id"] = connection_id
        requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")

def handle_admin_command(text, chat_id, conn_id):
    global global_bot_muted
    cmd = text.strip()

    # /all commands
    if cmd.lower() == "/all":
        help_text = (
            "👑 *PA BOT ADMIN COMMANDS LIST* 👑\n\n"
            "🔹 `/sleep <min>` ya `/sleep30min` : Bot ko is chat me utne minute sulane ke liye.\n"
            "🔹 `/wake` : Is chat me bot ko wapas turant active karne ke liye.\n"
            "🔹 `/silent on` / `/silent off` : Poore bot ko sabhi jagah mute ya unmute karne ke liye.\n"
            "🔹 `/sdl <chat_id> <HH:MM> <msg>` : Scheduled message set karne ke liye (24hr IST).\n"
            "🔹 `/status` : Check karein ki is chat me bot ka status kya hai."
        )
        send_reply(chat_id, help_text, conn_id)
        return True

    # /sleep logic (e.g. /sleep 30, /sleep30min, /sleep10m)
    sleep_match = re.match(r"^/sleep\s*(\d+)(?:min|m)?$", cmd.lower())
    if sleep_match:
        minutes = int(sleep_match.group(1))
        chat_sleep_until[chat_id] = time.time() + (minutes * 60)
        send_reply(chat_id, f"✅ Done! Bot ab is chat me agle {minutes} minute tak koi reply nahi dega.", conn_id)
        return True

    # /wake logic
    if cmd.lower() == "/wake":
        if chat_id in chat_sleep_until:
            del chat_sleep_until[chat_id]
        send_reply(chat_id, "⚡ Bot wapas active ho gaya hai is chat ke liye!", conn_id)
        return True

    # /silent on / off
    if cmd.lower() == "/silent on":
        global_bot_muted = True
        send_reply(chat_id, "🔇 Global Silent Mode ON! Bot kisi ko bhi reply nahi karega.", conn_id)
        return True
    if cmd.lower() == "/silent off":
        global_bot_muted = False
        send_reply(chat_id, "🔊 Global Silent Mode OFF! Bot wapas normal kaam karega.", conn_id)
        return True

    # /status
    if cmd.lower() == "/status":
        now = time.time()
        is_sleeping = chat_sleep_until.get(chat_id, 0) > now
        rem = int((chat_sleep_until.get(chat_id, 0) - now) / 60) if is_sleeping else 0
        status_msg = f"📊 Status:\n- Sleep: {'Haan (' + str(rem) + ' min bache)' if is_sleeping else 'Nahi'}\n- Global Mute: {'ON' if global_bot_muted else 'OFF'}"
        send_reply(chat_id, status_msg, conn_id)
        return True

    # /sdl schedule message (e.g. /sdl 12345678 15:30 Hello bhai)
    if cmd.lower().startswith("/sdl "):
        parts = cmd.split(" ", 3)
        if len(parts) >= 4:
            target_chat = parts[1]
            time_str = parts[2]
            sched_msg = parts[3]
            scheduled_tasks.append({
                "target_chat": target_chat,
                "time_str": time_str,
                "msg": sched_msg,
                "conn_id": conn_id
            })
            send_reply(chat_id, f"⏰ Message scheduled for {time_str} to `{target_chat}`: '{sched_msg}'", conn_id)
            return True
        else:
            send_reply(chat_id, "❌ Format galat hai! Use karein: `/sdl <chat_id> 15:30 Message yahan likhein`", conn_id)
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
    # 25-second wait window
    time.sleep(25)

    # Check agar Rehan ne in 25 sec ke andar reply kar diya
    last_rehan = rehan_last_reply_time.get(chat_id, 0)
    if last_rehan > msg_timestamp:
        return

    # Check agar chat sleep mode me hai
    if time.time() < chat_sleep_until.get(chat_id, 0):
        return

    # Check agar global bot mute hai
    if global_bot_muted:
        return

    # Night Mode check
    if is_night_time():
        send_reply(chat_id, "Rehan bhai abhi so rahe hain 😴, subah uthkar aapse baat karenge! Main unka PA hoon 😎🤝", conn_id)
        return

    # Agar Rehan pichle 10 minute me active the
    if (time.time() - last_rehan) < 600:
        busy_msg = "Abhi Rehan kuch kaam kar rahe hain, thode der baad msg karna. Main unka Personal Assistant hoon! 😎🤝"
        send_reply(chat_id, busy_msg, conn_id)
        return

    # Normal AI Reply via Gemini with typing effect
    try:
        requests.post(f"{BASE_URL}/sendChatAction", json={
            "chat_id": chat_id,
            "action": "typing",
            "business_connection_id": conn_id
        }, timeout=5)
    except Exception:
        pass

    ai_reply = get_ai_reply(chat_id, user_text)
    if not ai_reply:
        ai_reply = "Abhi Rehan kuch kaam kar rahe hain, thode der baad msg karna. Main unka Personal Assistant hoon! 😎🤝"

    send_reply(chat_id, ai_reply, conn_id)

def run_bot():
    print("🔥 PA OF REHANNN Supercharged Engine Running...")
    offset = None

    # Start Scheduler Thread
    st = threading.Thread(target=scheduler_worker)
    st.daemon = True
    st.start()

    while True:
        try:
            params = {"timeout": 20, "allowed_updates": ["business_message"]}
            if offset:
                params["offset"] = offset

            resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=30).json()

            for update in resp.get("result", []):
                offset = update["update_id"] + 1

                if "business_message" in update:
                    b_msg = update["business_message"]
                    msg_id = b_msg.get("message_id")

                    if msg_id in processed_msg_ids:
                        continue
                    processed_msg_ids.add(msg_id)
                    if len(processed_msg_ids) > 1000:
                        processed_msg_ids.clear()

                    chat_id = b_msg["chat"]["id"]
                    conn_id = b_msg.get("business_connection_id")
                    user_text = b_msg.get("text", "")
                    is_outbound = b_msg.get("is_outgoing", False)

                    # 1. OUTGOING (Jab aap khud msg bhejte hain)
                    if is_outbound:
                        rehan_last_reply_time[chat_id] = time.time()
                        # Check agar aapne koi admin command bheja hai
                        if user_text.startswith("/"):
                            handle_admin_command(user_text, chat_id, conn_id)
                        continue

                    # 2. INCOMING USER MESSAGE
                    if not user_text:
                        continue

                    # Sleep check
                    if time.time() < chat_sleep_until.get(chat_id, 0):
                        continue

                    # Delayed thread start
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
                
