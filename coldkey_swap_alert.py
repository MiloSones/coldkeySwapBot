import asyncio
import json
import math
import time
import requests
import websockets

import bittensor
from substrateinterface import SubstrateInterface, Keypair
from scalecodec.base import ScaleBytes
from scalecodec.types import Extrinsic


from dotenv import load_dotenv
import os

load_dotenv()


BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
WS_URL = os.getenv("WS_URL")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL"))
MNEMONIC = os.getenv("MNEMONIC")
VALIDATOR_HOTKEY = os.getenv("VALIDATOR_HOTKEY")



TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

keypair   = Keypair.create_from_mnemonic(MNEMONIC)
substrate = SubstrateInterface(url=WS_URL)
subtensor = bittensor.subtensor(network=WS_URL)
metadata = substrate.get_metadata()

seen_this_block = set()
current_block = None
last_block_time = 0
subnet_coldkeys = {}
subnet_count = 128


def decode_extrinsic(hex_string):
    xt = Extrinsic(data=ScaleBytes(hex_string), metadata=metadata)
    xt.decode()
    return xt

def get_pool_reserves(netuid):
    alpha_reserve = substrate.query(
        module='SubtensorModule',
        storage_function='SubnetAlphaIn',
        params=[netuid]
    ).value
    # query TAO in reserve
    tao_reserve = substrate.query(
        module='SubtensorModule',
        storage_function='SubnetTAO',
        params=[netuid]
    ).value
    return alpha_reserve, tao_reserve


async def add_stake_limit(hotkey,netuid,rao,slippage,tip=0):
    # slippage should be provided as multiplier e.g. 1.05 = 5%
    # {'hotkey': 'AccountId', 'netuid': 'u16', 'amount_staked': 'u64', 'limit_price': 'u64', 'allow_partial': 'bool'}

    pool_alpha,pool_tao = get_pool_reserves(netuid)
    price = pool_tao / pool_alpha
    limit_price = price * slippage
    call = substrate.compose_call(
        call_module='SubtensorModule',
        call_function='add_stake_limit',
        call_params={
            'hotkey': "5DXdHixxtCvoa6GHKs2Jgrdzc61882Ftx1zN2sYFQuwgL1S1",
            'netuid': netuid,
            'amount_staked': rao
            'limit_price': limit_price
            'allow_partial': False
        }
    )

    extrinsic = substrate.create_signed_extrinsic(
        call=call, keypair=keypair,tip=tip, era={'period': 1}
    )

    receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)

    if receipt.is_success:
        print(
            f"""
            Transaction successful:
            - Extrinsic Hash: {receipt.extrinsic_hash}
            - Block Hash: {receipt.block_hash}
            """
        )
    else:
        print(f"Transaction failed: {receipt.error_message}")

    return receipt


async def watch_new_blocks():
    global current_block, seen_this_block

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



async def poll_pending_extrinsics():
    global whale_staked_this_block

    req_id = 1000
    async with websockets.connect(WS_URL) as ws:
        while True:
            await ws.send(json.dumps({
                "jsonrpc":"2.0", "id":req_id,
                "method":"author_pendingExtrinsics", "params":[]
            }))
            resp = json.loads(await ws.recv())
            pendings = resp.get('result', [])

            for hx in pendings:
                if hx in seen_this_block:
                    continue

                try:
                    xt = decode_extrinsic(hx)
                except Exception:
                    continue

                # Check for coldkey swap
                try:
                    cm = xt.value['call']['call_module']
                    fn = xt.value['call']['call_function']
                    if cm == "SubtensorModule" and fn == "schedule_swap_coldkey":
                        caller = xt.value['address']
                        new_coldkey = None
                        for arg in xt.value['call']['call_args']:
                            if arg['name'] == 'new_coldkey':
                                new_coldkey = arg['value']

                        message = f"Coldkey swap scheduled:\nCaller: {caller}\nNew Coldkey: {new_coldkey}\nNetuid: {subnet_coldkeys[caller]}"
                        print(message)
                        try:
                            requests.post(TELEGRAM_URL, data={
                                "chat_id": GROUP_CHAT_ID,
                                "text": message,
                            })
                        except Exception as e:
                            print(f"[Telegram Error] {e}")
                        try:
                            add_stake_limit()
                        except Exception as e:
                            print(f"[Staking Error] {e}")

                except Exception as e:
                    print(f"[Decode Error] {e}")

                seen_this_block.add(hx)

            req_id += 1
            await asyncio.sleep(POLL_INTERVAL)





async def main():
    print("Getting subnet coldkeys")
    for netuid in range(1,subnet_count+1):
        subnet_coldkeys[subtensor.subnet(netuid).owner_coldkey] = netuid
    print("Starting watcher")
    await asyncio.gather(
        watch_new_blocks(),
        poll_pending_extrinsics()
    )

if __name__ == "__main__":
    asyncio.run(main())
