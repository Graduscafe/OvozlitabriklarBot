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
    # 1. ADMIN MIJOZGA JAVOB YOZSA (REPLY QILGANDA)
    if message.from_user.id == ADMIN_ID:
        if message.reply_to_message:
            target_id = None
            # Xabar matni yoki rasm tagidagi yozuvdan ID qidiramiz
            ref_text = message.reply_to_message.text or message.reply_to_message.caption or ""
            
            if "🆔 ID:" in ref_text:
                try:
                    # ID dan keyingi raqamlarni ajratib olamiz
                    target_id = int(ref_text.split("🆔 ID:")[1].strip().split()[0])
                except Exception as e:
                    logging.error(f"ID ajratishda xato: {e}")

            if target_id:
                try:
                    await bot.copy_message(chat_id=target_id, from_chat_id=ADMIN_ID, message_id=message.message_id)
                    await message.reply("✅ Xabar mijozga yetkazildi.")
                except Exception as e:
                    await message.reply(f"❌ Xabar bormadi (Mijoz botni bloklagan bo'lishi mumkin): {e}")
            else:
                await message.reply("⚠️ Xabarda ID topilmadi. Mijoz ma'lumotlari yozilgan xabarga 'Reply' qiling.")
        else:
            await message.reply("Javob berish uchun mijozning ma'lumotlari bor xabariga 'Reply' qiling.")

    # 2. MIJOZ ADMINGA YOZSA
    else:
        user = message.from_user
        msg_text = message.text or message.caption or "[Media xabar]"
        
        # Ma'lumotlarni bitta chiroyli blokga jamlaymiz
        admin_info = (
            f"👤 **Kimdan:** {user.full_name}\n"
            f"🔗 **Username:** @{user.username if user.username else 'yoq'}\n"
            f"🆔 ID: {user.id}\n"
            f"---------------------------\n"
            f"💬 **Xabar:**\n{msg_text}"
        )

        try:
            # Profil rasmini tekshiramiz
            photos = await bot.get_user_profile_photos(user.id, limit=1)
            
            if photos.total_count > 0:
                # Rasmi bo'lsa, ma'lumotlarni rasm tagida yuboramiz
                await bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=photos.photos[0][-1].file_id,
                    caption=admin_info,
                    parse_mode="Markdown"
                )
            else:
                # Rasmi bo'lmasa, faqat matnni o'zini yuboramiz
                await bot.send_message(ADMIN_ID, admin_info, parse_mode="Markdown")
            
            # Agar xabar matn bo'lmasa (rasm, audio, video), uni ham nusxalaymiz
            if not message.text:
                await bot.copy_message(chat_id=ADMIN_ID, from_chat_id=message.chat.id, message_id=message.message_id)
                
        except Exception as e:
            logging.error(f"Adminga yuborishda xato: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
