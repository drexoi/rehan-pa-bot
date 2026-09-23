import time
import requests
import google.generativeai as genai

BOT_TOKEN = "8809883023:AAFxaw4n1RZ2Jla5bzsHFWvrBLCaZbyWWAM"
GEMINI_KEY = "AQ.Ab8RN6Lo0gq3gr0XRWSnqMkDNPB_aEF2glR5NxmcNoPvY1DOjw"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Gemini Configure
genai.configure(api_key=GEMINI_KEY)

SYSTEM_PROMPT = """
You are the AI Personal Assistant (PA) of Rehan.
Identity Rules (CRITICAL):
- Agar koi puche 'tum kaun ho', 'who are you', 'kya naam hai', ya identity puche, strictly English me reply do: "I am Rehan's PA." (ya "I am Rehan's PA, how can I help you? 😎").

Chat Style & Personality:
- Aapko bilkul Rehan ke style me baat karni hai: ekdam casual, chill, cool aur natural Hinglish me (jaise dost log chat karte hain).
- Har message ka reply do, kisi ko ignore ya reject mat karo.
- Tone friendly aur mast honi chahiye. Emojis ka khoob use karo (🔥, 😂, 🤝, 💯, ✨, 🙌).
- Replies to the point aur 1-2 lines me rakho, zyada lambe boring bhashan mat dena.
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
        print(f"Send Error: {e}")

def main():
    bot_id = get_bot_id()
    print(f"🔥 PA OF REHANNN Bot live ho gaya hai! (Bot ID: {bot_id})")
    
    offset = None
    while True:
        try:
            params = {"timeout": 30, "allowed_updates": ["business_message"]}
            if offset:
                params["offset"] = offset

            resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=40).json()

            for update in resp.get("result", []):
                offset = update["update_id"] + 1

                # Business message handle karna
                if "business_message" in update:
                    b_msg = update["business_message"]
                    sender = b_msg.get("from", {})
                    
                    # Agar bot ka khud ka message ho toh ignore karo
                    if sender.get("id") == bot_id:
                        continue

                    user_text = b_msg.get("text")
                    if not user_text:
                        continue

                    chat_id = b_msg["chat"]["id"]
                    conn_id = b_msg.get("business_connection_id")

                    # AI Response
                    try:
                        ai_res = model.generate_content(user_text)
                        reply = ai_res.text.strip() if ai_res and ai_res.text else "Bolo bhai! Kya haal? 🔥"
                    except Exception:
                        reply = "Haan bhai bolo, kya scene hai? 🙌"

                    # Reply send karo
                    send_reply(chat_id, reply, conn_id)

        except Exception as err:
            time.sleep(2)

if __name__ == "__main__":
    main()
    
