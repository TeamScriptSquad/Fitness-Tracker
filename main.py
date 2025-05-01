from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

import add_exercise

# Токен бота
TOKEN = "7992184754:AAEUm6DZ5hcaDuWETV6ve8yn-BD1-vt0LKk"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def welcome(message: Message):
    user_name = message.from_user.first_name
    await message.answer(
        f"Здравствуйте, {user_name}! 👋\nЯ бот фитнес-трекер. Я помогу вам:\n"
        "   1) Составить план тренировок\n"
        "   2) Следить за вашей активностью\n"
        "   3) Контролировать питание\n"
        "   4) Не забывать о тренировках\n"
        "   5) Мотивировать\n"
        "   6) Составлять отчет о проделанной работе"
    )

# Обработчик команды /add_exercise
@dp.message(Command("add_exercise"))
async def add_exercise_handler(message: Message, state: FSMContext):
    await add_exercise.start_adding_exercise(message, state)

# Обработчик всех сообщений для добавления упражнения
@dp.message()
async def process_all_messages(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state in ["waiting_for_name", "waiting_for_sets",
                        "waiting_for_reps", "waiting_for_weight"]:
        await add_exercise.process_exercise_data(message, state, bot)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())