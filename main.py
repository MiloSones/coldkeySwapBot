from listener import poll_pending_extrinsics, watch_new_blocks
import asyncio


async def main():
    print("pending extrinsics: ")
    await asyncio.gather(
        poll_pending_extrinsics(),
        watch_new_blocks()
    )

if __name__ == "__main__":
    asyncio.run(main())