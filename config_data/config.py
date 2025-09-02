import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

LOCAL_ENV = os.getenv("LOCAL_ENV")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
REDIS_URL = os.getenv("REDIS_URL")
CURRENT_URL = os.getenv("CURRENT_URL", "https://wildslots.ru")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://wildslots.ru")
ROUTE_FOR_WEBHOOK = os.getenv("ROUTE_FOR_WEBHOOK", "/webhook")
PORT = os.getenv("PORT", 5003)
ADMINS = os.getenv("ADMINS").split(",")
CHATS = os.getenv("CHATS").split(",")


DEFAULT_COMMANDS = (
    ("start", "Запустить бота"),
    ("new_chat", "Добавить бота в чат"),
    ("general_stats", "Статистика"),
)
