import asyncio
import sys

from utils import get_client, get_config_dir


async def main(argv):
    config_dir = get_config_dir(argv)
    eas_client = get_client(config_dir)
    result = await eas_client.async_run_hosting_capacity_calibration(
        calibration_name="<calibration_name>",
        calibration_time_local="<timestamp>",
        feeders=["<feeder>"]
    )
    print(result)

    await eas_client.aclose()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
