import asyncio
import sys
from datetime import datetime

from zepben.eas.client.work_package import WorkPackageConfig, TimePeriod

from utils import get_client, get_config, print_result, get_config_dir


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)
    result = await eas_client.async_run_hosting_capacity_work_package(
        WorkPackageConfig(
            config["feeders"],
            config["forecast_years"],
            config["scenarios"],
            load_time=TimePeriod(
                start_time=datetime.fromisoformat(config["load_time"]["start"]),
                end_time=datetime.fromisoformat(config["load_time"]["end"])
            ),
            name=config["work_package_name"]
        )
    )

    print_result(result)
    await eas_client.aclose()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
