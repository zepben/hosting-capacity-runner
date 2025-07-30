import asyncio
import sys

from utils import get_client, get_config_dir

"""
Perform a calibration run which will utilise PQV data to model the network, and output voltage deltas between the PQV actuals and the
simulated network. Find more information on calibration at:
    https://zepben.github.io/evolve/docs/hosting-capacity-service/docs/next/how-to-guides/calibration#option-2-using-the-python-api

Use the returned result with monitor_calibration_run.py to monitor
"""

async def main(argv):
    config_dir = get_config_dir(argv)
    eas_client = get_client(config_dir)
    result = await eas_client.async_run_hosting_capacity_calibration(
        calibration_name="<calibration_name>",  # Any name - it will be stored alongside results.
        calibration_time_local="<timestamp>",   # The time of the PQV data to model
        feeders=["<feeder>"]                    # The feeders to model
    )
    print(result)

    await eas_client.aclose()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
