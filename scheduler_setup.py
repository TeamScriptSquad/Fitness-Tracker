from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# Можно добавить дополнительные настройки, например:
# - Очистку старых задач
# - Логирование ошибок