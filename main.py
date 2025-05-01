from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import stats
import save_templates
import add_exercise

# Токен бота (замените на свой)
TOKEN = "7992184754:AAEUm6DZ5hcaDuWETV6ve8yn-BD1-vt0LKk"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()


# Состояния для FSM (Finite State Machine)
class AddExercise(StatesGroup):
    waiting_for_name = State()
    waiting_for_sets = State()
    waiting_for_reps = State()
    waiting_for_weight = State()


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


# Обработчик команды /add_exercise - начинает диалог
@dp.message(Command("add_exercise"))
async def start_adding_exercise(message: Message, state: FSMContext):
    await message.answer("Введите название упражнения:")
    await state.set_state(AddExercise.waiting_for_name)


# Обработчик названия упражнения
@dp.message(AddExercise.waiting_for_name)
async def process_exercise_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите количество подходов:")
    await state.set_state(AddExercise.waiting_for_sets)


# Обработчик количества подходов
@dp.message(AddExercise.waiting_for_sets)
async def process_sets(message: Message, state: FSMContext):
    try:
        sets = int(message.text)
        if sets <= 0:
            raise ValueError
        await state.update_data(sets=sets)
        await message.answer("Введите количество повторений:")
        await state.set_state(AddExercise.waiting_for_reps)
    except ValueError:
        await message.answer("Пожалуйста, введите целое положительное число:")


# Обработчик количества повторений
@dp.message(AddExercise.waiting_for_reps)
async def process_reps(message: Message, state: FSMContext):
    try:
        reps = int(message.text)
        if reps <= 0:
            raise ValueError
        await state.update_data(reps=reps)
        await message.answer("Введите вес (кг), если упражнение без веса, введите 0:")
        await state.set_state(AddExercise.waiting_for_weight)
    except ValueError:
        await message.answer("Пожалуйста, введите целое положительное число:")


# Обработчик веса и финальное сохранение
@dp.message(AddExercise.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        if weight < 0:
            raise ValueError

        # Получаем все сохраненные данные
        data = await state.get_data()

        # Сохраняем упражнение
        add_exercise.log_workout(data['name'], data['sets'], data['reps'], weight)

        await message.answer(
            f"Упражнение сохранено!\n"
            f"Название: {data['name']}\n"
            f"Подходы: {data['sets']}\n"
            f"Повторения: {data['reps']}\n"
            f"Вес: {weight} кг"
        )

        # Сбрасываем состояние
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число (0 если без веса):")


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())