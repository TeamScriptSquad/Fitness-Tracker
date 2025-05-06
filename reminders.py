from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot


class ReminderManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.reminders = {}  # {user_id: [reminder1, reminder2]}

    async def add_reminder(self, user_id: int, reminder_type: str, time: str, text: str):
        """Добавление напоминания."""
        if user_id not in self.reminders:
            self.reminders[user_id] = []

        reminder = {
            "type": reminder_type,
            "time": time,
            "text": text
        }
        self.reminders[user_id].append(reminder)
        await self._schedule_reminder(user_id, reminder)

    async def _schedule_reminder(self, user_id: int, reminder: dict):
        """Планирование напоминания через APScheduler."""
        from scheduler_setup import scheduler

        time = datetime.strptime(reminder["time"], "%H:%M").time()
        scheduler.add_job(
            self._send_reminder,
            'cron',
            hour=time.hour,
            minute=time.minute,
            args=(user_id, reminder["text"])
        )

    async def _send_reminder(self, user_id: int, text: str):
        """Отправка напоминания пользователю."""
        await self.bot.send_message(user_id, f"🔔 Напоминание: {text}")

    async def load_reminders_from_db(self):
        """Загрузка напоминаний из БД (заглушка)."""
        # Здесь должна быть логика загрузки из PostgreSQL/SQLite
        pass