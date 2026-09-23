import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from google import genai

BOT_TOKEN = "8809883023:AAFxaw4n1RZ2Jla5bzsHFWvrBLCaZbyWWAM"
GEMINI_KEY = "AQ.Ab8RN6Lo0gq3gr0XRWSnqMkDNPB_aEF2glR5NxmcNoPvY1DOjw"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_KEY)

SYSTEM_PROMPT = """
You are acting as the AI Personal Assistant (PA) of Rehan.
Identity Rules:
- Agar koi puche "tum kaun ho", "who are you", ya tumhari identity ke baare me, toh strictly English me reply dena: "I am Rehan's PA." (ya "I am Rehan's PA, how can I help you? 😎").

Style & Behavior:
- Kabhi bhi kisi ka reply reject ya refuse mat karna. Har baat ka supportive, helpful aur badiya answer dena.
- Tone: Ekdam friendly, natural Hinglish aur chill vibe (jaise Rehan khud baat kar raha ho).
- Emojis ka natural aur mast use karo (jaise 🔥, 🤝, 😂, ✨, 🙌, 💯).
- Replies to the point, engaging aur cool hone chahiye (zyada lambe boring paragraphs nahi).
"""

@dp.business_message()
async def handle_business_message(message: Message):
    if not message.text:
        return

    try:
        await bot.send_chat_action(
            chat_id=message.chat.id,
            action="typing",
            business_connection_id=message.business_connection_id
        )
    except Exception:
        pass

    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message.text,
            config={
                "system_instruction": SYSTEM_PROMPT
            }
        )
        reply_text = response.text or "Aur batao bhai, kya scene hai? 🔥"
    except Exception:
        reply_text = "Haan bhai sun raha hu, bolo! 🙌"

    await bot.send_message(
        chat_id=message.chat.id,
        text=reply_text,
        business_connection_id=message.business_connection_id
    )

async def main():
    print("🔥 PA OF REHANNN Bot active ho gaya hai...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
