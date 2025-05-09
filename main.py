import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import logging
import asyncio
from aiogram.enums import ParseMode
from aiogram.types import Message

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = "7992184754:AAEUm6DZ5hcaDuWETV6ve8yn-BD1-vt0LKk"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Настройка Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'service_account.json'
SPREADSHEET_ID = '1prksexFd3Q7cG86JuLxOE3tqrVNsW-0TQq9C4iJvjWs'


# Инициализация Google Sheets
def init_google_sheets():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()


sheet = init_google_sheets()


# Проверка и создание листа при необходимости
def check_sheet_exists():
    try:
        spreadsheet = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = spreadsheet.get('sheets', [])

        sheet_names = [s['properties']['title'] for s in sheets]
        if 'Nutrition' not in sheet_names:
            body = {
                "requests": [{
                    "addSheet": {
                        "properties": {
                            "title": "Nutrition",
                            "gridProperties": {
                                "rowCount": 1000,
                                "columnCount": 10
                            }
                        }
                    }
                }]
            }
            sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

            headers = [
                ["Timestamp", "User ID", "Username", "Food Name", "Portion (g)",
                 "Calories", "Proteins (g)", "Fats (g)", "Carbs (g)", "Meal Type"]
            ]
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range="Nutrition!A1",
                valueInputOption="USER_ENTERED",
                body={"values": headers}
            ).execute()

    except Exception as e:
        logger.error(f"Error checking/creating sheet: {e}")


check_sheet_exists()


# Состояния FSM для питания
class NutritionStates(StatesGroup):
    waiting_for_food_name = State()
    waiting_for_portion = State()
    waiting_for_calories = State()
    waiting_for_proteins = State()
    waiting_for_fats = State()
    waiting_for_carbs = State()
    waiting_for_meal_type = State()


# Обработчик команды /start
@dp.message(Command("start"))
async def welcome(message: Message):
    user_name = message.from_user.first_name
    await message.answer(
        f"Привет, {user_name}! 👋\nЯ бот для учета питания.\n\n"
        "Доступные команды:\n"
        "/add_food - добавить прием пищи\n"
        "/food_diary - посмотреть дневник питания\n"
        "/nutrition_advice - получить рекомендации по КБЖУ"
    )


# Обработчик команды /add_food
@dp.message(Command("add_food"))
async def start_food_input(message: types.Message, state: FSMContext):
    await state.set_state(NutritionStates.waiting_for_food_name)
    await message.answer("Введите название продукта/блюда:")


@dp.message(NutritionStates.waiting_for_food_name)
async def process_food_name(message: types.Message, state: FSMContext):
    await state.update_data(food_name=message.text)
    await state.set_state(NutritionStates.waiting_for_portion)
    await message.answer("Введите размер порции (в граммах):")


@dp.message(NutritionStates.waiting_for_portion)
async def process_portion(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '').isdigit():
        await message.answer("Пожалуйста, введите число (граммы)")
        return

    await state.update_data(portion=message.text)
    await state.set_state(NutritionStates.waiting_for_calories)
    await message.answer("Введите количество калорий:")


@dp.message(NutritionStates.waiting_for_calories)
async def process_calories(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '').isdigit():
        await message.answer("Пожалуйста, введите число (калории)")
        return

    await state.update_data(calories=message.text)
    await state.set_state(NutritionStates.waiting_for_proteins)
    await message.answer("Введите количество белков (в граммах):")


@dp.message(NutritionStates.waiting_for_proteins)
async def process_proteins(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '').isdigit():
        await message.answer("Пожалуйста, введите число (белки)")
        return

    await state.update_data(proteins=message.text)
    await state.set_state(NutritionStates.waiting_for_fats)
    await message.answer("Введите количество жиров (в граммах):")


@dp.message(NutritionStates.waiting_for_fats)
async def process_fats(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '').isdigit():
        await message.answer("Пожалуйста, введите число (жиры)")
        return

    await state.update_data(fats=message.text)
    await state.set_state(NutritionStates.waiting_for_carbs)
    await message.answer("Введите количество углеводов (в граммах):")


@dp.message(NutritionStates.waiting_for_carbs)
async def process_carbs(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '').isdigit():
        await message.answer("Пожалуйста, введите число (углеводы)")
        return

    await state.update_data(carbs=message.text)
    await state.set_state(NutritionStates.waiting_for_meal_type)
    await message.answer("Выберите тип приема пищи:\n1. Завтрак\n2. Обед\n3. Ужин\n4. Перекус")


@dp.message(NutritionStates.waiting_for_meal_type)
async def process_meal_type(message: types.Message, state: FSMContext):
    meal_types = {
        "1": "Завтрак",
        "2": "Обед",
        "3": "Ужин",
        "4": "Перекус"
    }

    if message.text not in meal_types:
        await message.answer("Пожалуйста, выберите вариант из списка (1-4)")
        return

    meal_type = meal_types[message.text]
    user_data = await state.get_data()
    await state.clear()

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = message.from_user.id
    values = [
        current_time,
        str(user_id),
        message.from_user.first_name,
        user_data.get('food_name', ''),
        user_data.get('portion', ''),
        user_data.get('calories', ''),
        user_data.get('proteins', ''),
        user_data.get('fats', ''),
        user_data.get('carbs', ''),
        meal_type
    ]

    try:
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="Nutrition!A2",
            valueInputOption="USER_ENTERED",
            body={"values": [values]}
        ).execute()

        await message.answer(
            "✅ Данные о питании успешно сохранены!\n\n"
            f"🍽 {user_data['food_name']}\n"
            f"⏱ {current_time}\n"
            f"🍴 Порция: {user_data['portion']}г\n"
            f"🔥 Калории: {user_data['calories']}\n"
            f"🥩 Белки: {user_data['proteins']}г\n"
            f"🥑 Жиры: {user_data['fats']}г\n"
            f"🍞 Углеводы: {user_data['carbs']}г\n"
            f"🍽 Тип приема: {meal_type}"
        )
    except Exception as e:
        logger.error(f"Ошибка при записи в Google Sheets: {e}")
        await message.answer("⚠️ Произошла ошибка при сохранении данных")


# Обработчик команды /food_diary
@dp.message(Command("food_diary"))
async def show_food_diary(message: types.Message):
    try:
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Nutrition!A2:J"
        ).execute()

        values = result.get('values', [])
        user_records = [row for row in values if len(row) > 1 and row[1] == str(message.from_user.id)]

        if not user_records:
            await message.answer("Ваш дневник питания пуст.")
            return

        response = "📝 Ваши последние записи:\n\n"
        for record in user_records[-5:]:
            response += (
                f"🍽 {record[3]}\n"
                f"⏱ {record[0]}\n"
                f"🍴 Порция: {record[4]}г\n"
                f"🔥 Калории: {record[5]}\n"
                f"🥩 Белки: {record[6]}г | 🥑 Жиры: {record[7]}г | 🍞 Углеводы: {record[8]}г\n"
                f"🍽 Тип: {record[9] if len(record) > 9 else 'Не указан'}\n\n"
            )

        await message.answer(response)
    except Exception as e:
        logger.error(f"Ошибка при чтении из Google Sheets: {e}")
        await message.answer("⚠️ Произошла ошибка при загрузке данных")


# Обработчик команды /nutrition_advice
@dp.message(Command("nutrition_advice"))
async def nutrition_advice(message: types.Message):
    await message.answer(
        "Выберите вашу цель:\n"
        "1. Похудение\n"
        "2. Поддержание веса\n"
        "3. Набор мышечной массы\n\n"
        "Ответьте цифрой (1-3)"
    )


@dp.message(F.text.in_(["1", "2", "3"]))
async def process_nutrition_goal(message: types.Message):
    goals = {
        "1": {
            "title": "Похудение",
            "advice": "Рекомендуемый дефицит калорий: 10-20% от суточной нормы.\n"
                      "Белки: 1.6-2.2 г/кг веса\n"
                      "Жиры: 0.5-1 г/кг веса\n"
                      "Углеводы: остальные калории"
        },
        "2": {
            "title": "Поддержание веса",
            "advice": "Поддерживайте баланс калорий.\n"
                      "Белки: 1.2-1.6 г/кг веса\n"
                      "Жиры: 0.8-1.2 г/кг веса\n"
                      "Углеводы: остальные калории"
        },
        "3": {
            "title": "Набор мышечной массы",
            "advice": "Рекомендуемый профицит калорий: 10-15% от суточной нормы.\n"
                      "Белки: 1.6-2.2 г/кг веса\n"
                      "Жиры: 0.8-1.2 г/кг веса\n"
                      "Углеводы: остальные калории"
        }
    }

    goal = goals[message.text]
    await message.answer(
        f"🏆 Цель: {goal['title']}\n\n"
        f"📝 Рекомендации:\n{goal['advice']}\n\n"
        "Для точного расчета вашей индивидуальной нормы КБЖУ "
        "укажите ваш вес, рост, возраст и уровень активности."
    )


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())