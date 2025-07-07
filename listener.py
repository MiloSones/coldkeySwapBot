"""Event loop: watch Subtensor for new blocks & pending extrinsics."""

from __future__ import annotations

import asyncio
import json

import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

import config
from helpers import decode_extrinsic
from staking import add_stake
from telegram import printTG

MAX_RECONNECT_DELAY = 60  # seconds

# Guards access to `config.seen_this_block`
_seen_lock = asyncio.Lock()


async def safe_connect():
    """Connect with back‑off *and* rate‑limit to avoid hammering the node."""
    delay = 1
    while True:
        try:
            config.record_reconnect_attempt()
            if len(config.reconnect_attempts) > 20:
                await asyncio.sleep(60)

            return await websockets.connect(
                config.WS_URL, ping_interval=20, ping_timeout=10
            )
        except Exception as e:
            msg = f"[Reconnect Failed] Retrying in {delay}s: {e}"
            config.logger.error(msg, exc_info=True)
            printTG(msg)
            await asyncio.sleep(delay)
            delay = min(MAX_RECONNECT_DELAY, delay * 2)


async def poll_pending_extrinsics():
    req_id = 1000
    while True:
        ws = await safe_connect()
        try:
            async with ws:
                while True:
                    try:
                        await ws.send(
                            json.dumps(
                                {
                                    "jsonrpc": "2.0",
                                    "id": req_id,
                                    "method": "author_pendingExtrinsics",
                                    "params": [],
                                }
                            )
                        )
                        resp = json.loads(await ws.recv())
                        pendings = resp.get("result", [])
                    except (
                        ConnectionClosedError,
                        ConnectionClosedOK,
                        asyncio.TimeoutError,
                    ) as e:
                        msg = f"[WebSocket Closed - poll_pending_extrinsics] {e}"
                        config.logger.warning(msg)
                        printTG(msg)
                        break
                    except Exception as e:
                        msg = f"[WS/JSON Error - poll_pending_extrinsics] {e}"
                        config.logger.error(msg, exc_info=True)
                        printTG(msg)
                        pendings = []

                    for hx in pendings:
                        async with _seen_lock:
                            if hx in config.seen_this_block:
                                continue
                            config.seen_this_block.add(hx)
                        try:
                            xt = decode_extrinsic(hx)
                            if (
                                xt.value["call"]["call_function"]
                                == "schedule_swap_coldkey"
                            ):
                                caller = xt.value["address"]
                                new_coldkey = next(
                                    (
                                        arg["value"]
                                        for arg in xt.value["call"]["call_args"]
                                        if arg["name"] == "new_coldkey"
                                    ),
                                    None,
                                )
                                netuid = config.subnet_coldkeys.get(caller, -1)
                                if netuid != -1:
                                    add_stake(netuid)
                                else:
                                    printTG("Invalid netuid for caller %s" % caller)
                        except Exception as e:
                            msg = f"[Decode Hex Error] {e}"
                            printTG(msg)
                            config.logger.error(msg, exc_info=True)
                            continue
        except Exception as e:
            msg = f"[Unexpected Error in poll_pending_extrinsics] {e}"
            config.logger.error(msg, exc_info=True)
            printTG(msg)
            await asyncio.sleep(3)


async def watch_new_blocks():
    current_block = None
    while True:
        ws = await safe_connect()
        try:
            async with ws:
                await ws.send(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "chain_subscribeNewHeads",
                            "params": [],
                        }
                    )
                )
                _ = json.loads(await ws.recv())["result"]
                while True:
                    try:
                        data = json.loads(await ws.recv())
                        header = data.get("params", {}).get("result")
                        if not header:
                            continue
                        block_num = int(header["number"], 16)
                        if block_num != current_block:
                            current_block = block_num
                            async with _seen_lock:
                                config.seen_this_block.clear()
                            print(f"🧱 New block: {block_num}")
                    except (
                        ConnectionClosedError,
                        ConnectionClosedOK,
                        asyncio.TimeoutError,
                    ) as e:
                        msg = f"[WebSocket Closed - watch_new_blocks] {e}"
                        config.logger.warning(msg)
                        printTG(msg)
                        break
                    except Exception as e:
                        msg = f"[WS/JSON Error - watch_new_blocks] {e}"
                        config.logger.error(msg, exc_info=True)
                        printTG(msg)
        except Exception as e:
            msg = f"[Unexpected Error in watch_new_blocks] {e}"
            config.logger.error(msg, exc_info=True)
            printTG(msg)
            await asyncio.sleep(3)
