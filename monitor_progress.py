import asyncio
import sys

from utils import get_config_dir, get_client, print_progress
from zepben.eas import Query

exit_flag = False


async def print_loop(argv):
    config_dir = get_config_dir(argv)
    eas_client = get_client(config_dir)

    while not exit_flag:
        try:
            result = await  eas_client.query(Query.get_active_work_packages())
            print("Press Ctrl + C to stop monitor...")
            print_progress(result)
        except Exception as e:
            print(e)
        await asyncio.sleep(5)
    await eas_client.close()


asyncio.run(print_loop(sys.argv))
