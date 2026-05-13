import asyncio
import sys

from utils import get_client, get_config_dir, print_cancel
from zepben.eas import Mutation


async def main(argv):
    config_dir = get_config_dir(argv)
    eas_client = get_client(config_dir)
    work_package_id = input("Please enter ID of work package to cancel: ")
    try:
        result = await eas_client.mutation(Mutation.cancel_work_package(work_package_id))
        print_cancel(result)
    except Exception as e:
        print(e)

    await eas_client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
