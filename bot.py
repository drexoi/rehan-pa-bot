import time
import threading
import requests
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "PA OF REHANNN 24/7 Live!"

BOT_TOKEN = "8809883023:AAFxaw4n1RZ2Jla5bzsHFWvrBLCaZbyWWAM"
GEMINI_KEY = "AQ.Ab8RN6Lo0gq3gr0XRWSnqMkDNPB_aEF2glR5NxmcNoPvY1DOjw"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

SYSTEM_PROMPT = """
You are acting as the AI Personal Assistant (PA) of Rehan.
Identity Rules (STRICT):
- When someone asks 'who are you', 'tum kaun ho', or asks identity, reply in English: "I am Rehan's PA." (or "I am Rehan's PA, how can I help you? 😎").

Tone & Personality:
- Chat like a real person in natural, chill, friendly Hinglish.
- Emojis ka khoob use karo (🔥, 😂, 🤝, 💯, ✨, 🙌).
- Never refuse to answer. Short and crisp answers (1-2 sentences).
"""

# Already processed messages ko store karne ke liye taaki repeat na ho
processed_msg_ids = set()

def get_ai_reply(user_text):
    try:
        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [{
                "parts": [{"text": user_text}]
            }]
        }
        res = requests.post(GEMINI_URL, json=payload, timeout=10)
        data = res.json()
        
        # Text extract karna
        candidates = data.get("candidates", [])
        if candidates:
            reply = candidates[0]["content"]["parts"][0]["text"]
            return reply.strip()
        else:
            print("Gemini API Error:", data)
    except Exception as e:
        print("AI Exception:", e)
    return None

def send_reply(chat_id, text, connection_id):
    try:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "business_connection_id": connection_id
        }
        requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")

def run_bot():
    print("🔥 PA OF REHANNN Bot loop start ho gaya hai...")
    offset = None
    
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
                    
                    # 1. Loop protection: Ek hi message ko dubara process mat karo
                    if msg_id in processed_msg_ids:
                        continue
                    processed_msg_ids.add(msg_id)
                    
                    # Memory clear rakhne ke liye
                    if len(processed_msg_ids) > 1000:
                        processed_msg_ids.clear()

                    user_text = b_msg.get("text")
                    if not user_text:
                        continue

                    # 2. Self loop check (PA OF REHANNN ka apna reply ignore karo)
                    if "PA OF REHANNN" in user_text:
                        continue

                    chat_id = b_msg["chat"]["id"]
                    conn_id = b_msg.get("business_connection_id")

                    # Typing status show karna
                    try:
                        requests.post(f"{BASE_URL}/sendChatAction", json={
                            "chat_id": chat_id,
                            "action": "typing",
                            "business_connection_id": conn_id
                        }, timeout=5)
                    except Exception:
                        pass

                    # Gemini se reply
                    reply = get_ai_reply(user_text)
                    if not reply:
                        reply = "Haan bhai bolo, kya scene hai? 🔥"

                    send_reply(chat_id, reply, conn_id)

        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=10000)
    
