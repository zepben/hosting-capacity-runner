import asyncio
import sys
import threading

from utils import get_config_dir, get_client, print_progress

exit_flag = False


def keypress_monitor():
    global exit_flag
    input("Press ENTER to stop monitor...\n")
    exit_flag = True
    print("\nExiting the loop...")


async def print_loop(argv):
    config_dir = get_config_dir(argv)
    eas_client = get_client(config_dir)
    try:
        while not exit_flag:
            result = await eas_client.async_get_hosting_capacity_work_packages_progress()
            print_progress(result)
            await asyncio.sleep(5)
    finally:
        await eas_client.aclose()


async def main():
    thread = threading.Thread(target=keypress_monitor, daemon=True)
    thread.start()
    await print_loop(sys.argv)


asyncio.run(main())
