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
    if message.from_user.id != ADMIN_ID:
        text = (
            "Assalomu alaykum! 🤍\n\n"
            "**Yaqiningizga quvonch ulashishda bizni tanlaganingiz uchun tashakkur!** 🪽\n\n"
            "📥 **Buyurtma uchun dildagi so'zlaringizni shu yerga yozing...** ✍️\n\n"
            "🚀 **Ijodkorimiz tez orada sizga javob yozadi!** ✨"
        )
        await message.answer(text, parse_mode="Markdown")

@dp.message_handler(content_types=types.ContentTypes.ANY)
async def handle_messages(message: types.Message):
    # 1. ADMIN MIJOZGA JAVOB YOZSA
    if message.from_user.id == ADMIN_ID:
        if message.reply_to_message:
            target_id = None
            ref_text = message.reply_to_message.text or message.reply_to_message.caption or ""
            
            if "🆔 ID:" in ref_text:
                try:
                    target_id = int(ref_text.split("🆔 ID:")[1].strip())
                except: pass

            if target_id:
                try:
                    await bot.copy_message(chat_id=target_id, from_chat_id=ADMIN_ID, message_id=message.message_id)
                    await message.reply("✅ Xabar mijozga yetkazildi.")
                except Exception as e:
                    await message.reply(f"❌ Xatolik: {e}")
        else:
            await message.reply("Javob berish uchun xabarga 'Reply' qiling.")

    # 2. MIJOZ ADMINGA YOZSA (Ma'lumotlarni bitta xabarga jamlash)
    else:
        user = message.from_user
        full_name = user.full_name
        username = f"@{user.username}" if user.username else "Mavjud emas"
        user_id = user.id
        
        # Mijozning xabari nima ekanligini aniqlaymiz
        msg_text = message.text or message.caption or "[Media xabar]"
        
        # Adminga boradigan chiroyli ma'lumotlar jamlanmasi
        admin_text = (
            f"👤 **Kimdan:** {full_name}\n"
            f"🔗 **Username:** {username}\n"
            f"🆔 ID: {user_id}\n"
            f"---------------------------\n"
            f"💬 **Xabar:**\n{msg_text}"
        )

        try:
            # Profil rasmini olishga harakat qilamiz
            photos = await bot.get_user_profile_photos(user_id, limit=1)
            
            if photos.total_count > 0:
                # Agar profil rasmi bo'lsa, rasmni tagiga yozib yuboramiz
                await bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=photos.photos[0][-1].file_id,
                    caption=admin_text,
                    parse_mode="Markdown"
                )
            else:
                # Agar rasm bo'lmasa, faqat matnni o'zini yuboramiz
                await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
            
            # Agar xabar rasm, ovozli yoki video bo'lsa, uni alohida ham yuboramiz
            if not message.text:
                await bot.copy_message(chat_id=ADMIN_ID, from_chat_id=message.chat.id, message_id=message.message_id)
                
        except Exception as e:
            logging.error(f"Xatolik: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
