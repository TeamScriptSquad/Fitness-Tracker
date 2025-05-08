import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import logging
import asyncio
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(
    token="7992184754:AAEUm6DZ5hcaDuWETV6ve8yn-BD1-vt0LKk",  # Ваш токен
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # Установка HTML-разметки
)
dp = Dispatcher(storage=MemoryStorage())


# Состояния FSM
class NutritionStates(StatesGroup):
    waiting_for_food_name = State()
    waiting_for_portion = State()
    waiting_for_calories = State()
    waiting_for_proteins = State()
    waiting_for_fats = State()
    waiting_for_carbs = State()


# Настройка Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'service_account.json'
SPREADSHEET_ID = '1prksexFd3Q7cG86JuLxOE3tqrVNsW-0TQq9C4iJvjWs'

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


# Обработчик команды /add_food
@dp.message(F.text == '/add_food')
async def start_food_input(message: types.Message, state: FSMContext):
    await state.set_state(NutritionStates.waiting_for_food_name)
    await message.answer("Введите название продукта/блюда:")


# Остальные обработчики состояний
@dp.message(NutritionStates.waiting_for_food_name)
async def process_food_name(message: types.Message, state: FSMContext):
    await state.update_data(food_name=message.text)
    await state.set_state(NutritionStates.waiting_for_portion)
    await message.answer("Введите размер порции (в граммах):")


# Аналогично реализуйте остальные обработчики состояний...

# Обработчик команды /food_diary
@dp.message(F.text == '/food_diary')
async def show_food_diary(message: types.Message):
    try:
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Питание!A2:I"
        ).execute()

        values = result.get('values', [])
        user_records = [row for row in values if len(row) > 1 and row[1] == str(message.from_user.id)]

        if not user_records:
            await message.answer("Ваш дневник питания пуст.")
            return

        response = "📝 Ваши последние записи:\n\n"
        for record in user_records[-5:]:
            response += f"🍽 {record[3]}\n⏱ {record[0]}\n🍴 Порция: {record[4]}г\n"
            response += f"🔥 Калории: {record[5]}\n🥩 Белки: {record[6]}г | 🥑 Жиры: {record[7]}г | 🍞 Углеводы: {record[8]}г\n\n"

        await message.answer(response)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("⚠️ Произошла ошибка при загрузке данных")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())