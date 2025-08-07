import asyncio
import sys
from datetime import datetime

from utils import get_client, get_config_dir, fetch_feeders

"""
Perform a calibration run which will utilise PQV data to model the network, and output voltage deltas between the PQV actuals and the
simulated network. Find more information on calibration at:
    https://zepben.github.io/evolve/docs/hosting-capacity-service/docs/next/how-to-guides/calibration#option-2-using-the-python-api

Use the returned result with monitor_calibration_run.py to monitor
"""


async def main(argv):
    config_dir = get_config_dir(argv)
    eas_client = get_client(config_dir)
    feeder_mrids = ["<FEEDER_MRID>"]

    # To do a calibration run with all feeders, populate ewb_server in your auth_config.json file and uncomment the below.
    # This will use the SDK to fetch the network hierarchy and retrieve all the feeder mRIDs.
    # Note running all feeders will take significantly longer and has cost implications so should be performed with care.
    # feeders = await fetch_feeders(config_dir)
    # feeder_mrids = [f.mrid for f in feeders[:10]]   # Take only first 10 feeders to avoid running too many.

    try:
        result = await eas_client.async_run_hosting_capacity_calibration(
            calibration_name="<CALIBRATION_ID>",  # Any name - it will be stored alongside results.
            calibration_time_local=datetime(2025, month=7, day=12, hour=4, minute=0),  # The time of the PQV data to model. Note this time must be present in EWBs load database.
            feeders=feeder_mrids    # The feeders to model
        )
        print(result)
    except Exception as e:
        print(e)

    await eas_client.aclose()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
