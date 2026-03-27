import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, executor

# Sozlamalar
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Render port qidirishini to'xtatishi uchun kichik hiyla
async def on_startup(dp):
    logging.info("Bot ishga tushdi!")
    # Render kutayotgan portni "band" qilamiz
    if os.environ.get('PORT'):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', int(os.environ.get('PORT'))))
        s.listen(1)
        logging.info(f"Render uchun soxta port ochildi: {os.environ.get('PORT')}")

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        text = (
            "Assalomu alaykum! 🤍\n\n"
            "**Yaqiningizga quvonch ulashishda bizni tanlaganingiz uchun tashakkur!** 🪽\n\n"
            "Bu yerda sizni kutilmoqda:\n"
            "📞 **Audio tabrik** — Telefon orqali kutilmagan quvonch!\n"
            "✨ **Tug‘ilgan kun** uchun eng sara tabriklar\n"
            "✍️ **Eksklyuziv** va ma'noli tabrik sherlari\n"
            "🖼 **Ismlarga** yozilgan maxsus tabriknomalar\n\n"
            "📥 **Buyurtma uchun dildagi so'zlaringizni shu yerga yozing...** ✍️\n\n"
            "🚀 **Ijodkorimiz tez orada sizga javob yozadi!** ✨"
        )
        await message.answer(text, parse_mode="Markdown")
    else:
        await message.answer("Xush kelibsiz, Admin! Bot xizmatga tayyor.")

@dp.message_handler(content_types=['text', 'photo', 'audio', 'voice', 'video', 'document'])
async def handle_messages(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        if message.reply_to_message:
            target_id = None
            ref_text = message.reply_to_message.text or message.reply_to_message.caption or ""

            if "ID:" in ref_text:
                try:
                    target_id = int(ref_text.split("ID:")[1].strip())
                except: pass

            if target_id:
                try:
                    await bot.copy_message(chat_id=target_id, from_chat_id=ADMIN_ID, message_id=message.message_id)
                    await message.reply("✅ Xabar mijozga yetkazildi.")
                except Exception as e:
                    await message.reply(f"❌ Xabar bormadi: {e}")
        else:
            await message.reply("Javob yozish uchun mijoz xabariga 'Reply' qiling.")
    else:
        # Mijoz yozganda adminga yuborish
        info = f"\n\n---\n👤 Kimdan: {message.from_user.full_name}\n🆔 ID:{message.from_user.id}"
        try:
            await bot.copy_message(chat_id=ADMIN_ID, from_chat_id=message.chat.id, message_id=message.message_id)
            await bot.send_message(ADMIN_ID, info)
        except Exception as e:
            logging.error(f"Xatolik: {e}")

if __name__ == '__main__':
    # Botni ishga tushirishda on_startup funksiyasini qo'shdik
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
