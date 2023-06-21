import asyncio

from zepben.eas.client.work_package import WorkPackageConfig

from utils import get_client, get_feeders


async def main():
    feeders = get_feeders()
    eas_client = get_client()
    result = await eas_client.async_run_hosting_capacity_work_package(
        WorkPackageConfig(
            list(feeders),
            [2023],
            ["base"]
        )
    )

    if "data" in result:
        print(f'work_package_id={result["data"]["runHostingCapacity"]}')
    else:
        print(f"errors:\n{result['errors'].join(', ')}")

    await eas_client.aclose()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
