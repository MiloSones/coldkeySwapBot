"""Thin wrapper around Telegram Bot API with proper error handling."""

from __future__ import annotations

import requests
from requests import RequestException
import config


def printTG(message: str) -> None:
    """Send *message* to the configured chat.

    Errors are logged but not raised.
    """
    try:
        resp = requests.post(
            config.TELEGRAM_URL,
            data={"chat_id": config.TG_CHAT_ID, "text": message},
            timeout=10,
        )
        if resp.status_code != 200:
            config.logger.warning(
                "[Telegram HTTP %s] %s", resp.status_code, resp.text
            )
    except RequestException as exc:
        config.logger.error("[Telegram Error] %s", exc, exc_info=True)