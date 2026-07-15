import os
from dotenv import load_dotenv
load_dotenv()
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH', '')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise ValueError(
        "Не все обязательные переменные окружения заданы!\n"
        "Проверьте файл .env или переменные на хостинге.\n"
        "Необходимы: API_ID, API_HASH, BOT_TOKEN"
    )
PROXY_PORT = os.environ.get('PROXY_PORT')
PROXY_HOST = os.environ.get('PROXY_HOST')
if PROXY_PORT:
    PROXY_PORT = int(PROXY_PORT)
PROXY_SECRET = os.environ.get('PROXY_SECRET')

DB_PATH = 'data/deadlines.db'
EXPORT_PATH = 'data/exports/'

os.makedirs('data', exist_ok=True)
os.makedirs(EXPORT_PATH, exist_ok = True)
