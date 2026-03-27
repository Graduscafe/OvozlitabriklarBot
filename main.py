import os
import logging
from aiogram import Bot, Dispatcher, types, executor

# Sozlamalar
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    # Faqat mijozlarga start bosganda chiqadi
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
            "🚀 **Ijodkorimiz tez orada sizga javob yozadi va bayramingizni unutilmas qiladi!** ✨"
        )
        await message.answer(text, parse_mode="Markdown")
    else:
        await message.answer("Xush kelibsiz, Admin! Mijozlar yozsa, shu yerga ID bilan birga keladi.")

@dp.message_handler(content_types=['text', 'photo', 'audio', 'voice', 'video', 'document'])
async def handle_messages(message: types.Message):
    # 1. AGAR ADMIN JAVOB YOZAYOTGAN BO'LSA
    if message.from_user.id == ADMIN_ID:
        if message.reply_to_message:
            target_id = None
            
            # Xabar ichidan ID ni qidirish (ID:123456 ko'rinishida)
            ref_text = ""
            if message.reply_to_message.text:
                ref_text = message.reply_to_message.text
            elif message.reply_to_message.caption:
                ref_text = message.reply_to_message.caption

            if "ID:" in ref_text:
                try:
                    target_id = int(ref_text.split("ID:")[1].strip())
                except:
                    pass

            if target_id:
                try:
                    # Admin nima yuborsa (rasm, matn, ovoz) mijozga boradi
                    await bot.copy_message(chat_id=target_id, from_chat_id=ADMIN_ID, message_id=message.message_id)
                    await message.reply("✅ Xabar mijozga yetkazildi.")
                except Exception as e:
                    await message.reply(f"❌ Xabar bormadi. Balki mijoz botni bloklagandir?\n\n{e}")
            else:
                await message.reply("⚠️ Xabarda ID topilmadi. Reply qilayotgan xabaringizda 'ID:...' bo'lishi shart.")
        else:
            await message.reply("Mijozga javob yozish uchun uning xabariga 'Reply' qiling.")

    # 2. AGAR MIJOZ YOZAYOTGAN BO'LSA
    else:
        # Mijozning xabari adminga yuboriladi
        info = f"\n\n---\n👤 Kimdan: {message.from_user.full_name}\n🆔 ID:{message.from_user.id}"
        
        try:
            # Mijoz yozgan har qanday narsani (rasm, ovoz, matn) adminga nusxalaymiz
            await bot.copy_message(chat_id=ADMIN_ID, from_chat_id=message.chat.id, message_id=message.message_id)
            # Admin xabarni kimdan kelganini bilishi uchun ID ni alohida yuboramiz
            await bot.send_message(ADMIN_ID, info)
        except Exception as e:
            logging.error(f"Xatolik: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
