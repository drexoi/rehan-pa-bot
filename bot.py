import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
import google.generativeai as genai

BOT_TOKEN = "8809883023:AAFxaw4n1RZ2Jla5bzsHFWvrBLCaZbyWWAM"
GEMINI_KEY = "AQ.Ab8RN6Lo0gq3gr0XRWSnqMkDNPB_aEF2glR5NxmcNoPvY1DOjw"

# Gemini AI Configure
genai.configure(api_key=GEMINI_KEY)

# Aapki persona aur rules
SYSTEM_PROMPT = """
You are the AI Personal Assistant (PA) of Rehan.
Identity Rules (CRITICAL):
- Agar koi puche 'tum kaun ho', 'who are you', 'kya naam hai', ya puchhe identity ke baare me, strictly English me reply do: "I am Rehan's PA." (ya "I am Rehan's PA, how can I help you? 😎").

Chat Style & Personality:
- Aapko bilkul Rehan ke style me baat karni hai: ekdam casual, chill, cool aur natural Hinglish me (jaise dost aapas me WhatsApp ya Telegram pe chat karte hain).
- Har message ka reply do, kisi ko ignore ya reject mat karo.
- Tone bilkul friendly aur energetic honi chahiye.
- Natural tareeqe se mast emojis ka use karo (jaise 🔥, 😂, 🤝, 💯, ✨, 🙌, ⚡).
- Replies to the point, engaging aur seedhe rakho (chote 1-2 lines me, lambe robotic essays bilkul nahi).
- Bilkul bhi formal, boring corporate Hindi/English mat bolna.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

bot_user_id = None

@dp.business_message()
async def handle_business_message(message: Message):
    global bot_user_id
    
    # Text message check
    if not message.text:
        return
        
    # Agar bot ne khud message send kiya hai toh ignore karo taaki loop na bane
    if message.from_user and message.from_user.id == bot_user_id:
        return

    # Typing status dikhana
    try:
        await bot.send_chat_action(
            chat_id=message.chat.id,
            action="typing",
            business_connection_id=message.business_connection_id
        )
    except Exception:
        pass

    try:
        # AI se smart reply lena
        response = await asyncio.to_thread(model.generate_content, message.text)
        if response and response.text:
            reply_text = response.text.strip()
        else:
            reply_text = "Bolo bhai! Kya scene hai? 🔥"
    except Exception as e:
        print(f"Error: {e}")
        reply_text = "Haan sun raha hu bhai, bolo kya baat hai? 🙌"

    # Message bhejna
    await bot.send_message(
        chat_id=message.chat.id,
        text=reply_text,
        business_connection_id=message.business_connection_id
    )

async def main():
    global bot_user_id
    me = await bot.get_me()
    bot_user_id = me.id
    print(f"✅ PA OF REHANNN (@{me.username}) ab fully active hai!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
        
