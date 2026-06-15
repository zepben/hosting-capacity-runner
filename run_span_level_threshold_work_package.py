"""
This script provides an example of how to run a forecast work package for long term planning studies,
with span level rating configuration enabled for network simplification.
"""

import asyncio
import sys
from datetime import datetime

from zepben.eas import ForecastConfigInput, TimePeriodInput, WorkPackageInput, Mutation, HcGeneratorConfigInput, \
    HcModelConfigInput, HcSolveConfigInput, HcWriterConfigInput, HcWriterOutputConfigInput, \
    HcEnhancedMetricsConfigInput, HcStoredResultsConfigInput, HcMetricsResultsConfigInput, HcResultProcessorConfigInput

from utils import get_client, get_config, print_run, get_config_dir


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    # Work package with span level threshold config example.
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
                        # Use span level ratings (designedrating from CIM) during network simplification.
                        # Ensure rating_threshold is set to an appropriate value when enabling this.
                        useSpanLevelThreshold=True,
                        # Tolerable % difference between PLSI of connected AcLineSegments to normalise into a single impedance value.
                        simplifyPLSIThreshold=10.0,
                        # Tolerable % difference between span level ratings to collapse connected AcLineSegments into a single line.
                        ratingThreshold=10.0,
                        # Emergency current rating as a multiple of normal current rating (2.0 = 200% of normal).
                        emergAmpScaling=2.0
                    ),
                    solve=HcSolveConfigInput(stepSizeMinutes=30),
                ),

                resultProcessorConfig=HcResultProcessorConfigInput(
                    writerConfig=HcWriterConfigInput(
                        outputWriterConfig=HcWriterOutputConfigInput(
                            enhancedMetricsConfig=HcEnhancedMetricsConfigInput(
                                populateEnhancedMetrics=True,
                                populateEnhancedMetricsProfile=False,
                                calculateEmergForLoadThermal=True,
                                calculateNormalForLoadThermal=True,
                                calculateCO2=True,
                                populateConstraints=True,
                                populateWeeklyReports=True,
                                populateDurationCurves=True,
                                calculateEmergForGenThermal=True,
                                calculateNormalForGenThermal=True,
                            )
                        )
                    ),
                    # Caution: storing raw results uses significant storage — avoid for large work packages.
                    storedResults=HcStoredResultsConfigInput(
                        voltageExceptionsRaw=False,
                        overloadsRaw=True,
                        energyMetersRaw=False,
                        energyMeterVoltagesRaw=False
                    ),
                    # calculatePerformanceMetrics is deprecated — prefer populateEnhancedMetrics above.
                    metrics=HcMetricsResultsConfigInput(calculatePerformanceMetrics=False)
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
    asyncio.run(main(sys.argv))
