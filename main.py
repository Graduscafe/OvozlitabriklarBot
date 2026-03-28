import os
import logging
import asyncio
import threading
from aiohttp import web
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ChatType

# === SOZLAMALAR ===
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
GROUP_ID = int(os.getenv('GROUP_ID'))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Mijoz ID → Topic ID mapping
user_topic_map = {}
# Topic ID → Mijoz ID
topic_user_map = {}


# =============================================
# /start buyrug'i
# =============================================
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if message.chat.type != ChatType.PRIVATE:
        return
    if message.from_user.id != ADMIN_ID:
        text = (
            "Assalomu alaykum! 🤍\n\n"
            "Yaqiningizga quvonch ulashishda bizni tanlaganingiz uchun tashakkur! 🪽\n\n"
            "📥 Buyurtma uchun dildagi so'zlaringizni shu yerga yozing... ✍️\n\n"
            "🚀 Ijodkorimiz tez orada sizga javob yozadi! ✨"
        )
        await message.answer(text)


# =============================================
# Guruhdan admin yozsa → mijozga yetkazadi
# =============================================
@dp.message_handler(
    lambda msg: msg.chat.id == GROUP_ID and msg.from_user.id == ADMIN_ID,
    content_types=types.ContentTypes.ANY
)
async def handle_group_message(message: types.Message):
    if not message.message_thread_id:
        return

    target_id = topic_user_map.get(message.message_thread_id)

    if target_id:
        try:
            await bot.copy_message(
                chat_id=target_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
        except Exception as e:
            logging.error(f"Mijozga yuborishda xato: {e}")
            await bot.send_message(
                GROUP_ID,
                f"❌ Xabar bormadi: {e}",
                message_thread_id=message.message_thread_id
            )


# =============================================
# Mijozdan xabar kelsa → topic yaratadi yoki topadi
# =============================================
@dp.message_handler(
    lambda msg: msg.chat.type == ChatType.PRIVATE and msg.from_user.id != ADMIN_ID,
    content_types=types.ContentTypes.ANY
)
async def handle_user_message(message: types.Message):
    user = message.from_user
    user_id = user.id

    # Topic allaqachon bormi?
    if user_id not in user_topic_map:
        try:
            username_str = f"@{user.username}" if user.username else "username yo'q"
            topic_name = f"👤 {user.full_name}"

            # Yangi topic yaratamiz
            result = await bot.create_forum_topic(
                chat_id=GROUP_ID,
                name=topic_name
            )
            topic_id = result.message_thread_id

            # Mapping ga saqlaymiz
            user_topic_map[user_id] = topic_id
            topic_user_map[topic_id] = user_id

            # Topic ga mijoz ma'lumotlarini yuboramiz
            info_text = (
                f"👤 Mijoz: {user.full_name}\n"
                f"🔗 Username: {username_str}\n"
                f"🆔 ID: {user_id}\n\n"
                f"✍️ Bu yerda yozgan xabarlaringiz mijozga avtomatik yetkaziladi."
            )

            try:
                photos = await bot.get_user_profile_photos(user_id, limit=1)
                if photos.total_count > 0:
                    await bot.send_photo(
                        chat_id=GROUP_ID,
                        photo=photos.photos[0][-1].file_id,
                        caption=info_text,
                        message_thread_id=topic_id
                    )
                else:
                    await bot.send_message(
                        GROUP_ID,
                        info_text,
                        message_thread_id=topic_id
                    )
            except Exception:
                await bot.send_message(
                    GROUP_ID,
                    info_text,
                    message_thread_id=topic_id
                )

        except Exception as e:
            logging.error(f"Topic yaratishda xato: {e}")
            return

    topic_id = user_topic_map[user_id]

    # Xabarni topicga forward qilamiz
    try:
        await bot.forward_message(
            chat_id=GROUP_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            message_thread_id=topic_id
        )
    except Exception as e:
        logging.error(f"Topicga forwardda xato: {e}")


# =============================================
# RENDER UCHUN WEB SERVER
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
    t = threading.Thread(target=run_web_server, daemon=True)
    t.start()
    executor.start_polling(dp, skip_updates=True)
