from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message


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
        await state.update_data(name=message.text)
        await message.answer("Введите количество подходов:")
        await state.set_state("waiting_for_sets")

    elif current_state == "waiting_for_sets":
        try:
            sets = int(message.text)
            if sets <= 0:
                raise ValueError
            await state.update_data(sets=sets)
            await message.answer("Введите количество повторений:")
            await state.set_state("waiting_for_reps")
        except ValueError:
            await message.answer("Пожалуйста, введите целое положительное число:")

    elif current_state == "waiting_for_reps":
        try:
            reps = int(message.text)
            if reps <= 0:
                raise ValueError
            await state.update_data(reps=reps)
            await message.answer("Введите вес (кг), если упражнение без веса, введите 0:")
            await state.set_state("waiting_for_weight")
        except ValueError:
            await message.answer("Пожалуйста, введите целое положительное число:")

    elif current_state == "waiting_for_weight":
        try:
            weight = float(message.text)
            if weight < 0:
                raise ValueError

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
            await message.answer("Пожалуйста, введите число (0 если без веса):")