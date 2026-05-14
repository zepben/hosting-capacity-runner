import asyncio
import sys
from datetime import datetime

from zepben.eas import Mutation, WorkPackageInput, ForecastConfigInput, TimePeriodInput, HcGeneratorConfigInput, \
    HcModelConfigInput, HcFeederScenarioAllocationStrategy, HcSolveConfigInput, HcRawResultsConfigInput

from utils import get_client, get_config, print_run, get_config_dir

"""
This script provides an example of how to run a forecast work package with default load profile specified in the
ModelConfig so usage point without corresponding load profile in the database will use the provided profile instead
of blank.
"""


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    # Forecast Config example set up
    # This example is an extension of running a forecast work package, default load profile can also be applied to
    # feeder configs work packages too, similar to how override work packages also work with forecast work packages.
    forecast_config = ForecastConfigInput(
        feeders=config["feeders"],
        years=config["forecast_years"],
        scenarios=config["scenarios"],
        timePeriod=TimePeriodInput(
            startTime=datetime.fromisoformat(config["load_time"]["start1"]),
            endTime=datetime.fromisoformat(config["load_time"]["end1"]),
        )
    )

    # These profiles can be set up in configuration, or be hard coded as a list of values
    # The number of entries must match the expected number for the configured load_interval_length_hours (default to 0.5 if unset)
    # For load_interval_length_hours:
    #     0.25: 96 entries for daily and 35040 for yearly
    #     0.5: 48 entries for daily and 17520 for yearly
    #     1.0: 24 entries for daily and 8760 for yearly
    default_load_watts_profile = config["default_load_watts"]
    default_gen_watts_profile = config["default_gen_watts"]
    default_load_var_profile = config["default_load_var"]
    default_gen_var_profile = config["default_gen_var"]
    result = await eas_client.mutation(Mutation.run_work_package(
        WorkPackageInput(
            forecastConfig=forecast_config,
            generatorConfig=HcGeneratorConfigInput(
                model=HcModelConfigInput(
                    loadVMaxPu=1.2,
                    loadVMinPu=0.8,
                    pFactorBaseExports=-1,
                    pFactorBaseImports=1,
                    pFactorForecastPv=1,
                    fixSinglePhaseLoads=False,
                    maxSinglePhaseLoad=15000.0,
                    maxLoadServiceLineRatio=1.0,
                    maxLoadLvLineRatio=2.0,
                    maxLoadTxRatio=2.0,
                    maxGenTxRatio=4.0,
                    fixOverloadingConsumers=True,
                    fixUndersizedServiceLines=True,
                    feederScenarioAllocationStrategy=HcFeederScenarioAllocationStrategy.ADDITIVE,
                    closedLoopVRegEnabled=False,
                    closedLoopVRegSetPoint=0.9925,
                    seed=123,
                    loadIntervalLengthHours=1.0,
                    defaultLoadWatts=default_load_watts_profile,
                    defaultGenWatts=default_gen_watts_profile,
                    defaultLoadVar=default_load_var_profile,
                    defaultGenVar=default_gen_var_profile,
                ),
                solve=HcSolveConfigInput(stepSizeMinutes=30),
                rawResults=HcRawResultsConfigInput(
                    voltageExceptionsRaw=False,
                    overloadsRaw=True,
                    energyMetersRaw=False,
                    energyMeterVoltagesRaw=False,
                    resultsPerMeter=False
                ),
            )
        ),
        work_package_name=config["work_package_name"],
    ))

    print_run(result)
    await eas_client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
