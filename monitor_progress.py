import asyncio
import sys

from utils import get_config_dir, get_client, print_progress

exit_flag = False


async def print_loop(argv):
    config_dir = get_config_dir(argv)
    eas_client = get_client(config_dir)

    while not exit_flag:
        result = await eas_client.async_get_hosting_capacity_work_packages_progress()
        print("Press ENTER to stop monitor...")
        print_progress(result)
        await asyncio.sleep(5)
    await eas_client.aclose()


async def check_keypress(loop):
    def on_keypress():
        global exit_flag
        key = sys.stdin.read(1)
        if key == '\n':
            exit_flag = True
            print("\nExiting the loop...")

    loop.add_reader(sys.stdin, on_keypress)


async def main():
    loop = asyncio.get_event_loop()

    await asyncio.gather(
        check_keypress(loop),
        print_loop(sys.argv)
    )


asyncio.run(main())
