from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

# Разумные ограничения (можно настроить под свои нужды)
MAX_SETS = 20  # Максимальное количество подходов
MAX_REPS = 100  # Максимальное количество повторений в подходе
MAX_WEIGHT = 500  # Максимальный вес в кг
MAX_EXERCISE_LENGTH = 50  # Максимальная длина названия упражнения


def init_gsheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("FitnessTrackerLogs").sheet1


def log_workout(exercise, sets, reps, weight, comment=""):
    sheet = init_gsheet()
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d"),
        exercise, sets, reps, weight, comment
    ])


async def start_adding_exercise(message: Message, state: FSMContext):
    await message.answer("Введите название упражнения:")
    await state.set_state("waiting_for_name")


async def process_exercise_data(message: Message, state: FSMContext, bot: Bot):
    current_state = await state.get_state()

    if current_state == "waiting_for_name":
        exercise_name = message.text.strip()
        if len(exercise_name) > MAX_EXERCISE_LENGTH:
            await message.answer(f"Название слишком длинное. Максимум {MAX_EXERCISE_LENGTH} символов.")
            return
        elif not exercise_name:
            await message.answer("Название не может быть пустым.")
            return

        await state.update_data(name=exercise_name)
        await message.answer(f"Введите количество подходов (1-{MAX_SETS}):")
        await state.set_state("waiting_for_sets")

    elif current_state == "waiting_for_sets":
        try:
            sets = int(message.text)
            if sets <= 0:
                await message.answer(f"Число подходов должно быть положительным. Введите от 1 до {MAX_SETS}:")
            elif sets > MAX_SETS:
                await message.answer(f"Слишком много подходов. Максимум {MAX_SETS}. Введите меньше:")
            else:
                await state.update_data(sets=sets)
                await message.answer(f"Введите количество повторений в подходе (1-{MAX_REPS}):")
                await state.set_state("waiting_for_reps")
        except ValueError:
            await message.answer(f"Пожалуйста, введите целое число от 1 до {MAX_SETS}:")

    elif current_state == "waiting_for_reps":
        try:
            reps = int(message.text)
            if reps <= 0:
                await message.answer(f"Число повторений должно быть положительным. Введите от 1 до {MAX_REPS}:")
            elif reps > MAX_REPS:
                await message.answer(f"Слишком много повторений. Максимум {MAX_REPS}. Введите меньше:")
            else:
                await state.update_data(reps=reps)
                await message.answer(f"Введите вес в кг (0-{MAX_WEIGHT}), если без веса - 0:")
                await state.set_state("waiting_for_weight")
        except ValueError:
            await message.answer(f"Пожалуйста, введите целое число от 1 до {MAX_REPS}:")

    elif current_state == "waiting_for_weight":
        try:
            weight = float(message.text)
            if weight < 0:
                await message.answer(f"Вес не может быть отрицательным. Введите от 0 до {MAX_WEIGHT}:")
            elif weight > MAX_WEIGHT:
                await message.answer(f"Слишком большой вес. Максимум {MAX_WEIGHT} кг. Введите меньше:")
            else:
                data = await state.get_data()
                log_workout(data['name'], data['sets'], data['reps'], weight)

                await message.answer(
                    f"✅ Упражнение сохранено!\n"
                    f"🏋️‍♂️ Название: {data['name']}\n"
                    f"🔢 Подходы: {data['sets']}\n"
                    f"🔄 Повторения: {data['reps']}\n"
                    f"⚖️ Вес: {weight} кг"
                )

                await state.clear()
        except ValueError:
            await message.answer(f"Пожалуйста, введите число от 0 до {MAX_WEIGHT} (0 если без веса):")