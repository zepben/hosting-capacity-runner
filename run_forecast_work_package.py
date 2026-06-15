"""
This script provides an example of how to run a forecast work package for long term planning studies.
It allows you to configure a WorkPackage to run 10+ years of timeseries load flows for a given set of scenarios for a
configurable set of feeders.
"""

import asyncio
import sys
from datetime import datetime

from zepben.eas import ForecastConfigInput, TimePeriodInput, Mutation, WorkPackageInput, HcGeneratorConfigInput, \
    HcModelConfigInput, HcFeederScenarioAllocationStrategy, HcSolveConfigInput, \
    HcResultProcessorConfigInput, HcWriterConfigInput, HcWriterOutputConfigInput, HcEnhancedMetricsConfigInput, \
    HcStoredResultsConfigInput, HcMetricsResultsConfigInput

from utils import get_client, get_config, print_run, get_config_dir


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    # Forecast Config example set up
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
                        loadVMaxPu=1.2,
                        loadVMinPu=0.8,
                        # Override reactive power for base loads/generators using power factor instead of load profile VAr values.
                        # Set to null to use reactive power from load profiles instead.
                        pFactorBaseExports=-1,
                        pFactorBaseImports=1,
                        pFactorForecastPv=1,
                        # fixSinglePhaseLoads defaults to true - set False here to disable the single-phase load fixer.
                        fixSinglePhaseLoads=False,
                        maxSinglePhaseLoad=15000.0,
                        maxLoadServiceLineRatio=1.5,
                        maxLoadLvLineRatio=2.0,
                        maxLoadTxRatio=3.0,
                        maxGenTxRatio=10.0,
                        fixOverloadingConsumers=True,
                        fixUndersizedServiceLines=True,
                        feederScenarioAllocationStrategy=HcFeederScenarioAllocationStrategy.ADDITIVE,
                        # closedLoopVRegEnabled defaults to true. Set False to model regulators as-is from the network model.
                        closedLoopVRegEnabled=False,
                        seed=123,
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
                                populateConstraints=False,
                                populateWeeklyReports=False,
                                populateDurationCurves=False,
                                calculateEmergForGenThermal=True,
                                calculateNormalForGenThermal=True,
                            ))),
                    # Caution: storing raw results uses significant storage - avoid for large work packages.
                    storedResults=HcStoredResultsConfigInput(
                        voltageExceptionsRaw=False,
                        overloadsRaw=False,
                        energyMetersRaw=False,
                        energyMeterVoltagesRaw=False
                    ),
                    # calculatePerformanceMetrics is deprecated - prefer populateEnhancedMetrics above.
                    metrics=HcMetricsResultsConfigInput(calculatePerformanceMetrics=False)
                ),
                qualityAssuranceProcessing=False
            ),
            work_package_name=config["work_package_name"],
        ))
        print_run(result)
    except Exception as e:
        print(e)

    await eas_client.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
