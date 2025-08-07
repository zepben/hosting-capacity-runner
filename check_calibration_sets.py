import asyncio
import sys
import pprint

from utils import get_client, get_config_dir

"""
Get the IDs of all calibration runs.
"""


async def print_loop(argv):
    config_dir = get_config_dir(argv)
    eas_client = get_client(config_dir)

    try:
        result = await eas_client.async_get_hosting_capacity_calibration_sets()
        pprint.pprint(result)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(print_loop(sys.argv))
