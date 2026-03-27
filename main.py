import os
import logging
from aiogram import Bot, Dispatcher, types, executor

# Tokenni Render-dagi "Environment Variables"dan olamiz
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    text = (
        "Assalomu alaykum! 🤍\n\n"
        "**Yaqiningizga baxt ulashishda bizni tanlaganingiz uchun tashakkur!** 🪽\n\n"
        "Bu yerda sizni kutilmoqda:\n"
        "📞 **Audio tabrik** — Telefon orqali kutilmagan quvonch!\n"
        "✨ **Tug‘ilgan kun** uchun eng sara tabriklar\n"
        "✍️ **Eksklyuziv** va ma'noli tabrik sherlari\n"
        "🖼 **Ismlarga** yozilgan maxsus tabriknomalar\n\n"
        "📥 **Buyurtma uchun dildagi so'zlaringizni shu yerga yozing...** ✍️\n\n"
        "*Maxfiylik va samimiylik kafolatlanadi!* 🤫"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message_handler()
async def forward_to_admin(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        if message.reply_to_message and message.reply_to_message.forward_from:
            try:
                user_id = message.reply_to_message.forward_from.id
                await bot.send_message(user_id, message.text)
            except:
                await message.answer("Xatolik: Mijoz profilini yashirgan.")
    else:
        await message.forward(ADMIN_ID)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
