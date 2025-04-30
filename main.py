import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from aiogram import Router

router = Router()
# Загрузка переменных окружения
load_dotenv()

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GOOGLE_CLIENT_CONFIG = {
    "installed": {
        "auth_provider_x509_cert_url" : "https://www.googleapis.com/oauth2/v1/certs",
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri" : "https://oauth2.googleapis.com/token",
        "redirect_uris" : ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"],
        "project_id" : "fitness-tracker-bot",
    }
}
SCOPES = ['https://www.googleapis.com/auth/fitness.activity.read']

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Хранилище для токенов (Ваня, в реализованном боте лучше использовать в БД)
user_credentials = {}


async def get_google_fit_service(user_id):
    creds = user_credentials.get(user_id)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_config(GOOGLE_CLIENT_CONFIG, SCOPES, redirect_uri='http://localhost')
        auth_url, _  = flow.authorization_url(prompt='consent')

        await bot.send_message(user_id, f"Пожалуйста, авторизуйтесь по ссылке: {auth_url}")
        await bot.send_message(user_id, "После авторизации введите код, который вы получили:")

        # Ждем код от пользователя
        try:
            code = await wait_for_user_code(user_id)
            flow.fetch_token(code=code)
            creds = flow.credentials
            user_credentials[user_id] = creds
        except asyncio.TimeoutError:
            await bot.send_message(user_id, "Время ожидания истекло. Попробуйте снова.")
            return None

    return build('fitness', 'v1', credentials=creds)


async def wait_for_user_code(user_id, timeout=300):
    future = asyncio.get_event_loop().create_future()

    @router.message()
    async def handle_code(message: types.Message):
        if message.from_user.id == user_id:
            future.set_result(message.text)

    try:
        return await asyncio.wait_for(future, timeout)
    finally:
        router.message.unregister(handle_code)


async def get_steps_data(service, user_id):
    now = datetime.utcnow()
    start = now - timedelta(days=1)

    start_time_nanos = int(start.timestamp() * 1e9)
    end_time_nanos = int(now.timestamp() * 1e9)

    data_source = "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"

    try:
        dataset = service.users().dataSources().datasets().get(
            userId='me',
            dataSourceId=data_source,
            datasetId=f"{start_time_nanos}-{end_time_nanos}"
        ).execute()

        steps = 0
        if 'point' in dataset:
            for point in dataset['point']:
                for value in point['value']:
                    steps += value.get('intVal', 0)

        return steps
    except Exception as e:
        print(f"Error getting steps data: {e}")
        return None


@router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Привет! Я бот для отслеживания вашей активности через Google Fit.\n"
        "Используйте команду /steps чтобы увидеть количество шагов за сегодня."
    )


@router.message(Command("auth"))
async def auth_command(message: types.Message):
    await message.answer("Начинаем процесс авторизации...")
    service = await get_google_fit_service(message.from_user.id)
    if service:
        await message.answer("Авторизация успешна! Теперь вы можете получать данные из Google Fit.")


@router.message(Command("steps"))
async def steps_command(message: types.Message):
    service = await get_google_fit_service(message.from_user.id)
    if not service:
        return

    steps = await get_steps_data(service, message.from_user.id)
    if steps is not None:
        await message.answer(f"За последние 24 часа вы сделали {steps} шагов.")
    else:
        await message.answer("Не удалось получить данные о шагах. Попробуйте позже.")


async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())