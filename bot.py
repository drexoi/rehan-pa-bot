import time
import threading
import requests
from flask import Flask
import google.generativeai as genai

app = Flask(__name__)

@app.route("/")
def home():
    return "PA OF REHANNN Bot is active and running 24/7!"

BOT_TOKEN = "8809883023:AAFxaw4n1RZ2Jla5bzsHFWvrBLCaZbyWWAM"
GEMINI_KEY = "AQ.Ab8RN6Lo0gq3gr0XRWSnqMkDNPB_aEF2glR5NxmcNoPvY1DOjw"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

genai.configure(api_key=GEMINI_KEY)

SYSTEM_PROMPT = """
You are the AI Personal Assistant (PA) of Rehan.
Identity Rules (CRITICAL):
- Agar koi puche 'tum kaun ho', 'who are you', 'kya naam hai', strictly English me bolo: "I am Rehan's PA." (ya "I am Rehan's PA, how can I help you? 😎").

Chat Style & Personality:
- Aapko bilkul Rehan ke style me baat karni hai: chill, casual, friendly Hinglish me (jaise WhatsApp/Telegram pe dosto se baat hoti hai).
- Har message ka supportive aur mast reply do, kisi ko ignore ya reject mat karo.
- Emojis ka natural tareeqe se khoob use karo (🔥, 😂, 🤝, 💯, ✨, 🙌).
- Short aur engaging replies rakho (1-2 lines), boring formal paragraphs nahi.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

def get_bot_id():
    try:
        res = requests.get(f"{BASE_URL}/getMe").json()
        return res.get("result", {}).get("id")
    except Exception:
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
    bot_id = get_bot_id()
    print(f"🔥 PA OF REHANNN Bot running with ID: {bot_id}")
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
                    sender = b_msg.get("from", {})

                    # Khud ke message par trigger na ho
                    if sender.get("id") == bot_id:
                        continue

                    user_text = b_msg.get("text")
                    if not user_text:
                        continue

                    chat_id = b_msg["chat"]["id"]
                    conn_id = b_msg.get("business_connection_id")

                    try:
                        ai_res = model.generate_content(user_text)
                        reply = ai_res.text.strip() if ai_res and ai_res.text else "Bolo bhai! Kya scene hai? 🔥"
                    except Exception:
                        reply = "Haan bhai sun raha hu, bolo kya baat hai? 🙌"

                    send_reply(chat_id, reply, conn_id)

        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=10000)
    
