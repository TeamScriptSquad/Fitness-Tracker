from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

# Токен бота (замените на свой)
TOKEN = "YOUR_BOT_TOKEN"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Обработчик команды /start 
@dp.message(Command("start", "hello"))
async def welcome(message: Message):
    user_name = message.from_user.first_name
    await message.answer(f"Привет, {user_name}! 👋\nЯ бот, который умеет только приветствовать!")


# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
