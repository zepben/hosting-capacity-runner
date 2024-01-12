import asyncio
from datetime import datetime

from zepben.eas.client.work_package import WorkPackageConfig, ModelConfig, TimePeriod

from utils import get_client, get_config


async def main():
    config = get_config()
    eas_client = get_client()
    result = await eas_client.async_run_hosting_capacity_work_package(
        WorkPackageConfig(
            config["feeders"],
            config["forecast_years"],
            config["scenarios"],
            model_config=ModelConfig(
                load_time=TimePeriod(
                    start_time=datetime.fromisoformat(config["load_time"]["start"]),
                    end_time=datetime.fromisoformat(config["load_time"]["end"])
                )
            )
        )
    )

    if "data" in result:
        print(f'work_package_id={result["data"]["runHostingCapacityWorkPackage"]}')
    else:
        print(f"errors:\n{result['errors'].join(', ')}")

    await eas_client.aclose()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
