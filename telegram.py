from config import *
import requests

def printTG(message):
    try:
        requests.post(TELEGRAM_URL, data={
            "chat_id": TG_CHAT_ID,
            "text": message})
    except Exception as e:
        logger.error("[Telegram Error] %s", e, exc_info=True)