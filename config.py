from __future__ import annotations

"""Centralised configuration and runtime globals.

All mandatory values must be provided in the environment; optional values fall back
to sensible defaults so the application can start in a dev shell without a fully
populated .env.
"""

import logging
import os
import time
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _getenv_str(name: str, *, default: str | None = None) -> str:
    value = os.getenv(name)
    if not value:
        if default is None:
            raise RuntimeError(f"Environment variable {name} must be set")
        return default
    return value


def _getenv_int(name: str, *, default: int | None = None) -> int:
    try:
        return int(_getenv_str(name, default=str(default) if default is not None else None))
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an int") from exc


# --------------------------------------------------------------------------- #
# Required env vars
# --------------------------------------------------------------------------- #
BOT_TOKEN = _getenv_str("TG_BOT_TOKEN")
TG_CHAT_ID = _getenv_str("TG_CHAT_ID")
WS_URL = _getenv_str("WS_URL")
MNEMONIC = _getenv_str("MNEMONIC")

# Optional tuning knobs
POLL_INTERVAL = _getenv_int("POLL_INTERVAL", default=5)   # seconds

# Staking parameters
STAKE_AMOUNT = 6 * 10 ** 9       # planck units
TIP_AMOUNT = 1 * 10 ** 7
SLIPPAGE = Decimal("1.3")       # multiplier

# Units
NANO = 10 ** 9

# Misc
VALIDATOR_HOTKEY = _getenv_str("VALIDATOR_HOTKEY", default="5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1")
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logging.basicConfig(
    filename="errors.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("subtensor-bot")

# --------------------------------------------------------------------------- #
# Runtime globals (mutable)
# --------------------------------------------------------------------------- #
seen_this_block: set[str] = set()
subnet_coldkeys: dict[str, int] = {}
subnet_count: int = 128

# Track reconnect attempts for throttling
reconnect_attempts: list[float] = []


def record_reconnect_attempt() -> None:
    """Remember a reconnect attempt timestamp (called from listener.safe_connect)."""
    reconnect_attempts.append(time.monotonic())
    # keep only last minute
    horizon = time.monotonic() - 60
    while reconnect_attempts and reconnect_attempts[0] < horizon:
        reconnect_attempts.pop(0)

