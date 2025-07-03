from dotenv import load_dotenv
import os
import logging

load_dotenv()

POLL_INTERVAL    = int(os.getenv("POLL_INTERVAL"))
BOT_TOKEN        = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID       = os.getenv("TG_CHAT_ID")
WS_URL           = os.getenv("WS_URL")
MNEMONIC         = os.getenv("MNEMONIC")

# stake config
STAKE_AMOUNT = 6*10**9
TIP_AMOUNT = 1 *10**7
SLIPPAGE = 1.3
VALIDATOR_HOTKEY = "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1"

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

logging.basicConfig(
    filename='errors.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

#globals
seen_this_block = set()

subnet_coldkeys = {}
subnet_count = 128