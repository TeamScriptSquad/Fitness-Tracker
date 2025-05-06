import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from scheduler_setup import scheduler
from reminders import ReminderManager

# Новый способ настройки бота (для aiogram 3.7.0+)
bot = Bot(
    token="7992184754:AAEUm6DZ5hcaDuWETV6ve8yn-BD1-vt0LKk",
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
reminder_manager = ReminderManager(bot)

# Команда /start
@dp.message(F.text == '/start')
async def start(message: types.Message):
    await message.answer("Привет! Я твой фитнес-трекер. Используй /set_reminder чтобы установить напоминание.")

# Команда /set_reminder
@dp.message(F.text.startswith('/set_reminder'))
async def set_reminder(message: types.Message):
    args = message.text.split()[1:]  # Извлекаем аргументы без команды
    if len(args) < 3:
        await message.answer(
            "Формат: /set_reminder <тип> <время> <текст>\nПример: /set_reminder тренировка 18:30 'Пора на тренировку!'")
        return

    reminder_type = args[0]  # тренировка/вода/еда
    time = args[1]  # 18:30
    text = " ".join(args[2:])  # Текст напоминания

    user_id = message.from_user.id
    await reminder_manager.add_reminder(user_id, reminder_type, time, text)
    await message.answer(f"Напоминание установлено на {time}!")

async def on_startup():
    scheduler.start()
    asyncio.create_task(reminder_manager.load_reminders_from_db())

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())