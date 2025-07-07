from __future__ import annotations

from decimal import Decimal

import config
from helpers import get_pool_reserves
from subtensor import keypair, substrate
from telegram import printTG


def _price_per_alpha(pool_tao: int, pool_alpha: int) -> Decimal:
    """Return TAO/alpha as a high‑precision Decimal."""
    return Decimal(pool_tao) / Decimal(pool_alpha)


def add_stake(netuid: int) -> bool:
    pool_alpha, pool_tao = get_pool_reserves(netuid)

    if pool_alpha < 10 ** 15:  # 1 Pα threshold
        msg = "Low alpha likely not active, not staking"
        print(msg)
        printTG(msg)
        return False

    price = _price_per_alpha(pool_tao, pool_alpha)
    limit_price_nano = int(price * config.SLIPPAGE * config.NANO)

    message = (
        f"Staking {config.STAKE_AMOUNT} at {price:.10f} TAO/α on subnet {netuid}"
    )
    print(message)
    printTG(message)

    call = substrate.compose_call(
        call_module="SubtensorModule",
        call_function="add_stake",
        call_params={
            "validator_hotkey": config.VALIDATOR_HOTKEY,
            "amount": config.STAKE_AMOUNT,
            "limit_price": limit_price_nano,
            "netuid": netuid,
        },
    )

    extrinsic = substrate.create_signed_extrinsic(
        call=call, keypair=keypair, tip=config.TIP_AMOUNT, era={"period": 1}
    )
    receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)

    if receipt.is_success:
        msg = (
            f"✅ Transaction successful: {receipt.extrinsic_hash} in {receipt.block_hash}"
        )
    else:
        msg = f"❌ Transaction failed: {receipt.error_message}"

    print(msg)
    printTG(msg)
    return receipt.is_success