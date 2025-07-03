from helpers import decode_extrinsic
from staking import add_stake
from config import *
import websockets
import json
import asyncio



async def poll_pending_extrinsics():
    req_id = 1000
    async with websockets.connect(WS_URL) as ws:
        while True:
            try:
                await ws.send(json.dumps({
                    "jsonrpc":"2.0", "id":req_id,
                    "method":"author_pendingExtrinsics", "params":[]
                }))
                resp = json.loads(await ws.recv())
                pendings = resp.get('result', [])
            except Exception as e:
                logger.error("[WS/JSON Error] %s", e, exc_info=True)
                pendings = []

            for hx in pendings:
                if hx in seen_this_block:
                    continue
                try:
                    xt = decode_extrinsic(hx)
                    if(xt.value['call']['call_function'] == "schedule_swap_coldkey"):
                        caller = xt.value['address']
                        new_coldkey = next(
                            (arg['value'] for arg in xt.value['call']['call_args']
                             if arg['name']=='new_coldkey'),
                            None
                        )
                        netuid = subnet_coldkeys.get(caller, -1)
                        if (netuid != -1):
                            add_stake(netuid)
                        else:
                            print("Invalid netuid")
                            printTG("Invalid netuid")
                except Exception as e:
                    print(e)
                    printTG(e)
                    logger.error("[Decode Hex Error] %s", e, exc_info=True)
                    continue
                seen_this_block.add(hx)

            req_id += 1
            await asyncio.sleep(POLL_INTERVAL)

async def watch_new_blocks():
    current_block = None
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({
            "jsonrpc": "2.0", "id": 1,
            "method": "chain_subscribeNewHeads", "params": []
        }))
        sub_id = json.loads(await ws.recv())['result']
        while True:
            data = json.loads(await ws.recv())
            header = data.get('params', {}).get('result')
            if not header:
                continue
            block_num = int(header['number'], 16)
            if block_num != current_block:
                current_block = block_num
                seen_this_block.clear()
                print(f"🧱 New block: {block_num}")
