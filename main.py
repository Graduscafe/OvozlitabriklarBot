import os
import logging
import asyncio
import threading
from aiohttp import web
from aiogram import Bot, Dispatcher, types, executor

# === SOZLAMALAR ===
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# =============================================
# /start buyrug'i
# =============================================
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        text = (
            "Assalomu alaykum! 🤍\n\n"
            "Yaqiningizga quvonch ulashishda bizni tanlaganingiz uchun tashakkur! 🪽\n\n"
            "📥 Buyurtma uchun dildagi so'zlaringizni shu yerga yozing... ✍️\n\n"
            "🚀 Ijodkorimiz tez orada sizga javob yozadi! ✨"
        )
        await message.answer(text)


# =============================================
# Barcha xabarlarni qabul qiluvchi handler
# =============================================
@dp.message_handler(content_types=types.ContentTypes.ANY)
async def handle_messages(message: types.Message):

    # 1. ADMIN MIJOZGA JAVOB YOZSA
    if message.from_user.id == ADMIN_ID:
        if message.reply_to_message:
            target_id = None

            ref_text = (
                message.reply_to_message.text or
                message.reply_to_message.caption or
                ""
            )

            if "🆔 ID:" in ref_text:
                try:
                    after_id = ref_text.split("🆔 ID:")[1].strip()
                    target_id = int(after_id.split()[0])
                except Exception as e:
                    logging.error(f"ID ajratishda xato: {e}")

            if target_id:
                try:
                    await bot.copy_message(
                        chat_id=target_id,
                        from_chat_id=message.chat.id,
                        message_id=message.message_id
                    )
                    await message.reply("✅ Xabar mijozga yetkazildi.")
                except Exception as e:
                    logging.error(f"Mijozga yuborishda xato: {e}")
                    await message.reply(
                        f"❌ Xabar bormadi.\n"
                        f"Sabab: {e}\n\n"
                        f"(Mijoz botni bloklagan bo'lishi mumkin)"
                    )
            else:
                await message.reply(
                    "⚠️ Xabarda ID topilmadi.\n"
                    "Mijoz ma'lumotlari yozilgan xabarga 'Reply' qiling."
                )
        else:
            await message.reply(
                "ℹ️ Javob berish uchun mijozning xabariga 'Reply' qiling."
            )

    # 2. MIJOZ ADMINGA YOZSA
    else:
        user = message.from_user
        msg_text = message.text or message.caption or "[Media xabar]"
        username_str = f"@{user.username}" if user.username else "username yo'q"

        admin_info = (
            f"👤 Kimdan: {user.full_name}\n"
            f"🔗 Username: {username_str}\n"
            f"🆔 ID: {user.id}\n"
            f"{'─' * 27}\n"
            f"💬 Xabar:\n{msg_text}"
        )

        try:
            photos = await bot.get_user_profile_photos(user.id, limit=1)

            if photos.total_count > 0:
                await bot.send_photo(
                    chat_id=ADMIN_ID,
                    photo=photos.photos[0][-1].file_id,
                    caption=admin_info
                )
            else:
                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=admin_info
                )

            if not message.text:
                await bot.copy_message(
                    chat_id=ADMIN_ID,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id
                )

        except Exception as e:
            logging.error(f"Adminga yuborishda xato: {e}")


# =============================================
# RENDER UCHUN WEB SERVER (alohida thread)
# =============================================
def run_web_server():
    async def handle_health(request):
        return web.Response(text="Bot ishlayapti!")

    async def web_main():
        app = web.Application()
        app.router.add_get("/", handle_health)
        port = int(os.getenv("PORT", 10000))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logging.info(f"Web server {port}-portda ishga tushdi")
        await asyncio.sleep(3600 * 24 * 365)

    asyncio.run(web_main())


# =============================================
# ISHGA TUSHIRISH
# =============================================
if __name__ == '__main__':
    # Web server alohida threadda ishga tushadi
    t = threading.Thread(target=run_web_server, daemon=True)
    t.start()

    # Bot asosiy threadda ishlaydi
    executor.start_polling(dp, skip_updates=True)
