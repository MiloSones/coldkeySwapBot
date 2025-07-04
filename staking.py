from config import *
from helpers import get_pool_reserves
from subtensor import keypair, substrate

def add_stake(netuid):
    pool_alpha, pool_tao = get_pool_reserves(netuid)

    if (pool_alpha < 10*15):
        print("Low alpha likely not active, not staking")
        printTG("Low alpha likely not active, not staking")
        return False
    price = pool_tao / pool_alpha
    limit_price = price * SLIPPAGE * 10 ** 9
    message = f"Staking {STAKE_AMOUNT} at {price} on subnet {netuid}"
    print(message)
    printTG(message)
    call = substrate.compose_call(
            call_module='SubtensorModule',
            call_function='add_stake_limit',
            call_params={
                'hotkey': VALIDATOR_HOTKEY,
                'netuid': netuid,
                'amount_staked': STAKE_AMOUNT,
                'limit_price': int(limit_price),
                'allow_partial': False
            }
        )
    extrinsic = substrate.create_signed_extrinsic(
            call=call, keypair=keypair, tip=TIP_AMOUNT, era={'period': 1}
    )
    receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)

    if receipt.is_success:
        print(f"✅ Transaction successful: {receipt.extrinsic_hash} in {receipt.block_hash}")
        printTG(f"✅ Transaction successful: {receipt.extrinsic_hash} in {receipt.block_hash}")
        return True
    else:
        print(f"❌ Transaction failed: {receipt.error_message}")
        printTG(f"❌ Transaction failed: {receipt.error_message}")
        return False


