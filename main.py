from listener import poll_pending_extrinsics, watch_new_blocks
from config import *
from subtensor import subtensor
import asyncio


async def main():
    print("Getting subnet keys")
    for netuid in range(1, subnet_count+1):
        subnet_coldkeys[subtensor.subnet(netuid).owner_coldkey] = netuid
    print("pending extrinsics: ")
    await asyncio.gather(
        poll_pending_extrinsics(),
        watch_new_blocks()
    )
    # print(subnet_coldkeys["5CqTmNfgDchxULD1bfoz8jvj9rDYSoq76kiq98oBUUEDpWqX"])

if __name__ == "__main__":
    asyncio.run(main())