import time
import threading
import requests
from flask import Flask
from google import genai

app = Flask(__name__)

@app.route("/")
def home():
    return "PA OF REHANNN 24/7 Live!"

BOT_TOKEN = "8809883023:AAHfH_Z_KqD4UPltDJWSJnvfwBEv22flMVQ"
GEMINI_KEY = "AQ.Ab8RN6Jofq6-T63jgpwRRUQy3cv8cC5VY25s8L4W2BTCDLHqbA"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

ai_client = genai.Client(api_key=GEMINI_KEY)

SYSTEM_PROMPT = """
You are acting as the AI Personal Assistant (PA) of Rehan.
Identity Rules (STRICT):
- When someone asks 'who are you', 'tum kaun ho', or asks identity, reply in English: "I am Rehan's PA." (or "I am Rehan's PA, how can I help you? 😎").

Tone & Personality:
- Chat like a real person in natural, chill, friendly Hinglish (jaise WhatsApp/Telegram pe dost aapas me baat karte hain).
- Har message ka reply do, kisi ko ignore ya reject mat karo.
- Emojis ka khoob use karo (🔥, 😂, 🤝, 💯, ✨, 🙌).
- Short and crisp answers (1-2 sentences max), robotic bhashan bilkul mat dena.
"""

processed_msg_ids = set()
rehan_active_chats = {}

def get_ai_reply(user_text):
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config={
                "system_instruction": SYSTEM_PROMPT
            }
        )
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print("Gemini API Error:", e)
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
    print("🔥 PA OF REHANNN Smart Bot start ho gaya hai...")
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
                    
                    if msg_id in processed_msg_ids:
                        continue
                    processed_msg_ids.add(msg_id)
                    if len(processed_msg_ids) > 1000:
                        processed_msg_ids.clear()

                    chat_id = b_msg["chat"]["id"]
                    conn_id = b_msg.get("business_connection_id")
                    user_text = b_msg.get("text", "")

                    # Agar message khud Rehan ne bheja hai (Outgoing)
                    is_outbound = b_msg.get("is_outgoing", False)
                    if is_outbound:
                        # Rehan active ho gaya, agle 10 min ke liye bot chup rahega
                        rehan_active_chats[chat_id] = time.time()
                        continue

                    # Agar Rehan pichle 10 minute me chat kar chuka hai toh bot beech me nahi aayega
                    if chat_id in rehan_active_chats:
                        elapsed = time.time() - rehan_active_chats[chat_id]
                        if elapsed < 600:
                            continue
                        else:
                            del rehan_active_chats[chat_id]

                    if not user_text:
                        continue

                    # Typing action
                    try:
                        requests.post(f"{BASE_URL}/sendChatAction", json={
                            "chat_id": chat_id,
                            "action": "typing",
                            "business_connection_id": conn_id
                        }, timeout=5)
                    except Exception:
                        pass

                    reply = get_ai_reply(user_text)
                    if not reply:
                        reply = "Bolo bhai! Kya scene hai? 🔥"

                    send_reply(chat_id, reply, conn_id)

        except Exception as err:
            time.sleep(2)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=10000)
 
