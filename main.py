from __future__ import annotations

import asyncio

import config
from listener import poll_pending_extrinsics, watch_new_blocks
from subtensor import subtensor


async def main():
    print("Getting subnet keys")
    for netuid in range(1, config.subnet_count + 1):
        config.subnet_coldkeys[
            subtensor.subnet(netuid).owner_coldkey
        ] = netuid
    print("Starting listeners...")
    await asyncio.gather(
        poll_pending_extrinsics(),
        watch_new_blocks(),
    )


if __name__ == "__main__":
    asyncio.run(main())
