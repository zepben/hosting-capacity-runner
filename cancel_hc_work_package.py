import asyncio
import sys

from utils import get_client, print_result, get_config_dir


async def main(argv):
    config_dir = get_config_dir(argv)
    eas_client = get_client(config_dir)
    result = await eas_client.async_cancel_hosting_capacity_work_package(
        "<work_package_id_to_cancel>"
    )

    print_result(result)
    await eas_client.aclose()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
