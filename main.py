from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

# Токен бота (замените на свой)
TOKEN = "7992184754:AAEUm6DZ5hcaDuWETV6ve8yn-BD1-vt0LKk"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def welcome(message: Message):
    user_name = message.from_user.first_name
    await message.answer(f"Здравствуйте, {user_name}! 👋\nЯ бот фитнес-трекер. Я помогу вам:\n   1)Составить план тренировок\n   2)Следить за вашей активностью\n   3)Контролировать питание\n   4)Не забывать о тренировках\n   5)Мотивировать\n   6)Составлять отсчет о проделанной работе")



# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())