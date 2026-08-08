import asyncio
from datetime import datetime
import os
import json
import logging
from telethon import TelegramClient, events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import UserStatusOnline, UserStatusOffline, UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth

# ========== ДЕРЖИ ХУЙ ==========
API_ID = 33222575
API_HASH = "30e5784b4f338125540c2a4c98974cc0"
OWNER_ID = 6414838630

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = TelegramClient("session_session", API_ID, API_HASH)

# ========== ХУИСТИКА ==========
user_activity = {}
ACTIVITY_FILE = "activity_data.json"

def load_activity():
    global user_activity
    if os.path.exists(ACTIVITY_FILE):
        try:
            with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_activity = {int(k): v for k, v in data.items() if isinstance(v, list) and len(v) == 4}
                logger.info(f"Загружена статистика для {len(user_activity)} пользователей")
        except Exception as e:
            logger.error(f"Ошибка загрузки статистики: {e}")
            user_activity = {}
    else:
        user_activity = {}

def save_activity():
    try:
        with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
            json.dump(user_activity, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")

# ========== ПРИВЕТСТВИЯ ==========
DATA_FILE = "welcomed_users.txt"

def load_welcomed():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip().isdigit())
    return set()

def save_welcomed(user_id):
    with open(DATA_FILE, "a") as f:
        f.write(f"{user_id}\n")

already_welcomed = load_welcomed()

# ========== ОПРЕДЕЛЕНИЕ ДАТЫ ==========
def get_user_creation_date(user_id: int):
    thresholds = [
        (12000000000, 2030), (11000000000, 2029), (10000000000, 2028),
        (9000000000, 2027), (8000000000, 2026), (7000000000, 2025),
        (6000000000, 2024), (5000000000, 2023), (2000000000, 2022),
        (1800000000, 2021), (1500000000, 2020), (1300000000, 2019),
        (1000000000, 2018), (700000000, 2017), (400000000, 2016),
        (200000000, 2015), (10000000, 2014)
    ]
    year = 2013
    for threshold, y in thresholds:
        if user_id >= threshold:
            year = y
            break
    month = (user_id % 12) + 1
    day = (user_id % 28) + 1
    if year > datetime.now().year:
        year = datetime.now().year
    return datetime(year, month, day).strftime("%d.%m.%Y")

# ========== ФОРМИРОВАНИЕ ИНФОРМАЦИИ ==========
async def get_full_user_info(target_user):
    try:
        full_user = await client(GetFullUserRequest(target_user))
        user_full = full_user.users[0] if full_user.users else target_user
        full_info = full_user.full_user
    except Exception as e:
        logger.error(f"Ошибка получения full_user: {e}")
        user_full = target_user
        full_info = None

    first_name = user_full.first_name or "Без имени"
    username = f"@{user_full.username}" if user_full.username else "нет"
    bio = full_info.about if full_info and hasattr(full_info, 'about') and full_info.about else "нет"
    is_premium = "💎 Есть" if getattr(user_full, 'premium', False) else "Нет"

    common_groups = 0
    try:
        common_chats = await client.get_common_chats(target_user.id)
        common_groups = len(common_chats)
    except Exception:
        common_groups = -1
    groups_str = f"{common_groups}" if common_groups >= 0 else "Неизвестно"

    stats = user_activity.get(target_user.id, [0, 0, 0, 0])
    active_str = f"{stats[0]} | {stats[1]} | {stats[2]} | {stats[3]}"
    total_msgs = sum(stats)
    status_text = "Малоактивный аккаунт" if total_msgs < 10 else "Активный пользователь"

    real_date = None
    if hasattr(user_full, 'date') and user_full.date and user_full.date > 0:
        real_date = datetime.fromtimestamp(user_full.date)

    if real_date and real_date < datetime.now():
        created_date_str = real_date.strftime("%d.%m.%Y")
        days_ago = (datetime.now() - real_date).days
        age_str = f"{days_ago} дн." if days_ago >= 0 else "❓"
    else:
        created_date_str = get_user_creation_date(target_user.id)
        try:
            dt_epoch = datetime.strptime(created_date_str, "%d.%m.%Y")
            days_ago = (datetime.now() - dt_epoch).days
            age_str = f"{days_ago} дн." if days_ago >= 0 else "❓"
        except:
            age_str = "❓"

    text = f"""
🗓 <b>Информация о пользователе</b>

<code>{first_name} | {target_user.id}</code>

🕒 Во вселенной Telegram: <b>~ {created_date_str}</b>
🆔 ID: <code>{target_user.id}</code>
👤 Username: {username}
⭐ Telegram Premium: <b>{is_premium}</b>
📝 Био: <i>{bio}</i>
👥 Общих групп: {groups_str}
📅 Регистрация (дней назад): {age_str}

💬 Общий актив: <b>{active_str}</b>
❗️ {status_text}

• сгенерировано ботом от @yuSK1Z🌸 •
"""
    return text

# ========== ОБРАБОТЧИКИ ==========
@client.on(events.NewMessage(incoming=True, outgoing=True))
async def info(event):
    # Определяем отправителя
    sender = await event.get_sender()
    
    # --- 1. Автоответ новым пользователям (только в ЛС) ---
    if event.is_private and not event.out:
        if sender and hasattr(sender, 'bot') and not sender.bot and sender.id != OWNER_ID:
            if sender.id not in user_activity:
                user_activity[sender.id] = [0, 0, 0, 0]

            if event.text and not event.media:
                user_activity[sender.id][0] += 1
            elif event.photo or event.video:
                user_activity[sender.id][1] += 1
            elif event.voice or event.audio:
                user_activity[sender.id][2] += 1
            elif event.sticker:
                user_activity[sender.id][3] += 1

            save_activity()

            if str(sender.id) not in already_welcomed:
                already_welcomed.add(str(sender.id))
                save_welcomed(sender.id)

                info_text = await get_full_user_info(sender)
                await event.reply(info_text, parse_mode="html")
                logger.info(f"Автоответ новому пользователю {sender.id}")
                return

    # --- 2. Команды .info и /info (работают везде: ЛС, группы, каналы) ---
    if event.text and event.text.lower() in (".info", "/info"):
        # Проверяем, что отправитель команды — владелец (и это пользователь)
        if not sender or not hasattr(sender, 'id'):
            return
        if sender.id != OWNER_ID:
            await event.reply("⛔ Эта команда доступна только владельцу.")
            return

        target_user = None

        # Если есть реплай — берём пользователя из реплая
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            if reply_msg:
                target_user = await reply_msg.get_sender()

        # Если есть аргумент (username/id/phone)
        if not target_user and event.text:
            parts = event.text.split(maxsplit=1)
            if len(parts) > 1:
                arg = parts[1].strip()
                try:
                    entity = await client.get_entity(arg)
                    target_user = entity
                except:
                    try:
                        entity = await client.get_entity(int(arg))
                        target_user = entity
                    except:
                        try:
                            entity = await client.get_entity(arg)
                            target_user = entity
                        except:
                            pass

        # Если ничего не нашли — берём самого владельца
        if not target_user:
            target_user = await client.get_entity(OWNER_ID)

        # Убеждаемся, что target_user — пользователь (не канал, не группа)
        if hasattr(target_user, 'id') and not hasattr(target_user, 'broadcast'):
            info_text = await get_full_user_info(target_user)
            if event.out:
                await event.edit(info_text, parse_mode="html")
            else:
                await event.reply(info_text, parse_mode="html")
            logger.info(f"Владелец запросил информацию о {target_user.id}")
        else:
            await event.reply("❌ Невозможно получить информацию о канале или группе.")

# ========== ЗАПУСК ==========
async def main():
    load_activity()
    print("⏳ Ожидание... Введи номер телефона и код в консоли.")
    await client.start()
    print("✅ Юзербот запущен. В ЛС — автоответ новым, в группах — только .info для владельца.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
