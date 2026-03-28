import os
import logging
import asyncio
import threading
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ChatType
import asyncpg

# === SOZLAMALAR ===
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
GROUP_ID = int(os.getenv('GROUP_ID'))
DATABASE_URL = os.getenv('DATABASE_URL')
RENDER_URL = os.getenv('RENDER_URL', 'https://ovozlitabriklarbot.onrender.com')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# DB connection pool
db_pool = None


# =============================================
# DATABASE - jadval yaratish va CRUD
# =============================================
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    async with db_pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_topics (
                user_id BIGINT PRIMARY KEY,
                topic_id BIGINT NOT NULL
            )
        ''')
    logging.info("Database tayyor!")

async def get_topic_id(user_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT topic_id FROM user_topics WHERE user_id = $1', user_id
        )
        return row['topic_id'] if row else None

async def get_user_id(topic_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT user_id FROM user_topics WHERE topic_id = $1', topic_id
        )
        return row['user_id'] if row else None

async def save_mapping(user_id: int, topic_id: int):
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO user_topics (user_id, topic_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET topic_id = $2
        ''', user_id, topic_id)


# =============================================
# O'z-o'zini har 2 daqiqada ping qiladi
# =============================================
async def self_ping():
    await asyncio.sleep(30)  # Bot ishga tushguncha kut
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                await session.get(RENDER_URL, timeout=aiohttp.ClientTimeout(total=10))
            logging.info("Self-ping ✅")
        except Exception as e:
            logging.error(f"Self-ping xatosi: {e}")
        await asyncio.sleep(120)  # 2 daqiqa


# =============================================
# Topic yaratish (to'g'ridan API orqali)
# =============================================
async def create_forum_topic(chat_id: int, name: str) -> int:
    url = f"https://api.telegram.org/bot{API_TOKEN}/createForumTopic"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"chat_id": chat_id, "name": name}) as resp:
            data = await resp.json()
            if data.get("ok"):
                return data["result"]["message_thread_id"]
            else:
                raise Exception(data.get("description", "Topic yaratishda xato"))


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

    target_id = await get_user_id(message.message_thread_id)

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

    topic_id = await get_topic_id(user_id)

    if not topic_id:
        try:
            username_str = f"@{user.username}" if user.username else "username yo'q"
            topic_name = f"👤 {user.full_name}"

            topic_id = await create_forum_topic(GROUP_ID, topic_name)
            await save_mapping(user_id, topic_id)

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
async def handle_health(request):
    return web.Response(text="Bot ishlayapti!")

def run_web_server():
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
async def on_startup(dp):
    await init_db()
    asyncio.ensure_future(self_ping())

if __name__ == '__main__':
    t = threading.Thread(target=run_web_server, daemon=True)
    t.start()
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
