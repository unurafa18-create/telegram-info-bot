from datetime import datetime
from telethon import TelegramClient, events

api_id = 33222575
api_hash = "30e5784b4f338125540c2a4c98974cc0"

client = TelegramClient("session", api_id, api_hash)


# Функция для примерного определения даты по ID Telegram
def get_user_creation_date(user_id: int):
  # Примерные пороги ID и дат регистрации в Telegram
  # Источник: открытые данные сообщества по исследованию ID Telegram
  epochs = [
      (0, datetime(2013, 8, 1)),
      (10000000, datetime(2014, 1, 1)),
      (200000000, datetime(2015, 1, 1)),
      (400000000, datetime(2016, 1, 1)),
      (700000000, datetime(2017, 1, 1)),
      (1000000000, datetime(2018, 1, 1)),
      (1300000000, datetime(2019, 1, 1)),
      (1500000000, datetime(2020, 1, 1)),
      (1800000000, datetime(2021, 1, 1)),
      (2000000000, datetime(2022, 1, 1)),
      (5000000000, datetime(2023, 1, 1)),
      (6000000000, datetime(2024, 1, 1)),
      (7000000000, datetime(2025, 1, 1)),
  ]

  for threshold, dt in reversed(epochs):
    if user_id >= threshold:
      return dt.strftime("%d.%m.%Y")
  return "Не удалось определить"


@client.on(events.NewMessage(incoming=True))
async def info(event):
  if not event.is_private:
    return

  user = await event.get_sender()
  if not user:
    return

  created = get_user_creation_date(user.id)

  first_name = user.first_name or "Без имени"
  username = f"@{user.username}" if user.username else "нет"

  text = f"""
🗓 <b>Информация о пользователе</b>

<code>{first_name} | {user.id}</code>

🕒 Во вселенной Telegram: <b>~ {created}</b>
🆔 ID: <code>{user.id}</code>
👤 Username: {username}

💬 Общий актив: <b>0 | 0 | 0 | 0</b>
❗️ Малоактивный аккаунт

• сгенерировано вашим юзерботом •
"""

  await event.reply(text, parse_mode="html")


client.start()
client.run_until_disconnected()
