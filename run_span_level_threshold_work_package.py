import asyncio
import sys
from datetime import datetime

from zepben.eas import ForecastConfigInput, TimePeriodInput, WorkPackageInput, Mutation, HcGeneratorConfigInput, \
    HcModelConfigInput, HcSolveConfigInput, HcRawResultsConfigInput, HcWriterConfigInput, HcWriterOutputConfigInput, \
    HcEnhancedMetricsConfigInput, HcStoredResultsConfigInput, HcMetricsResultsConfigInput, HcResultProcessorConfigInput

from utils import get_client, get_config, print_run, get_config_dir

"""
This script provides an example of how to run a forecast work package for long term planning studies.
It allows you to configure a WorkPackage to run 10+ years of timeseries load flows for a given set of scenarios for a
configurable set of feeders. It is a minimal set up with example value added for span level rating related configuration
"""


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    # Work package with span level threshold Config example set up
    # This can be set up through the config file or by hard coding in the variables below.
    # The below will run a forecast-based work package for the configured feeders, years, and scenarios, over the time period specified in load_time below.
    # Note load_time reflects the base year (historical) load, and must be correctly specified to be a period of load data that exists in your system.
    # Consult your EWB HCM administrator if you do not know what load is available in your environment.
    forecast_config = ForecastConfigInput(
        feeders=config["feeders"],
        years=config["forecast_years"],
        scenarios=config["scenarios"],
        timePeriod=TimePeriodInput(
            startTime=datetime.fromisoformat(config["load_time"]["start1"]),
            endTime=datetime.fromisoformat(config["load_time"]["end1"]),
        )
    )

    try:
        result = await eas_client.mutation(Mutation.run_work_package(
            WorkPackageInput(
                forecastConfig=forecast_config,
                generatorConfig=HcGeneratorConfigInput(
                    model=HcModelConfigInput(
                        seed=123,
                        simplifyNetwork=True,
                        useSpanLevelThreshold=True,  # Use span level threshold during network simplification
                        simplifyPLSIThreshold=10.0,
                        # The tolerable % of difference between per length sequence impedance of connected AcLineSegment to normalize their value into a single set of values.
                        ratingThreshold=10.0,
                        # The tolerable % of difference between span level rating or rated current of connected AcLineSegment to collapse into a single line.
                        emergAmpScaling=2.0  # The scaling ratio of emergency current base on normal current.
                    ),
                    solve=HcSolveConfigInput(stepSizeMinutes=30),
                    rawResults=HcRawResultsConfigInput()
                ),

                resultProcessorConfig=HcResultProcessorConfigInput(
                    writerConfig=HcWriterConfigInput(
                        outputWriterConfig=HcWriterOutputConfigInput(
                            enhancedMetricsConfig=HcEnhancedMetricsConfigInput()
                        )
                    ),
                    storedResults=HcStoredResultsConfigInput(),
                    metrics=HcMetricsResultsConfigInput(calculatePerformanceMetrics=True)
                ),
                qualityAssuranceProcessing=True
            ),
            work_package_name=config["work_package_name"],
        ))
        print_run(result)
    except Exception as e:
        print(e)

    await eas_client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
