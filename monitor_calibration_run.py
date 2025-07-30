import asyncio
import sys
import pprint

from utils import get_client, get_config_dir

"""
Get the status of a calibration run.

Use the ID returned from the server in run_calibration.py
"""

CALIBRATION_ID = "<calibration_id>"  # ID of run to track


async def print_loop(argv):
    config_dir = get_config_dir(argv)
    eas_client = get_client(config_dir)

    print("Press Ctrl+C to exit")
    while True:
        result = await eas_client.async_get_hosting_capacity_calibration_run(id=CALIBRATION_ID)
        pprint.pprint(result)
        await asyncio.sleep(5)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(print_loop(sys.argv))
