"""
This script provides an example of how to run a forecast work package with a default load profile specified in the
ModelConfig, so usage points without a corresponding load profile in the database will use the provided profile instead
of blank.
"""

import asyncio
import sys
from datetime import datetime

from zepben.eas import Mutation, WorkPackageInput, ForecastConfigInput, TimePeriodInput, HcGeneratorConfigInput, \
    HcModelConfigInput, HcFeederScenarioAllocationStrategy, HcSolveConfigInput

from utils import get_client, get_config, print_run, get_config_dir


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    # Forecast Config example set up
    # This example is an extension of running a forecast work package. Default load profiles can also be applied to
    # feeder configs work packages in the same way.
    forecast_config = ForecastConfigInput(
        feeders=config["feeders"],
        years=config["forecast_years"],
        scenarios=config["scenarios"],
        timePeriod=TimePeriodInput(
            startTime=datetime.fromisoformat(config["load_time"]["start1"]),
            endTime=datetime.fromisoformat(config["load_time"]["end1"]),
        )
    )

    # These profiles can be set up in configuration, or be hard coded as a list of values.
    # The number of entries must match the expected number for the configured load_interval_length_hours (default 0.5).
    # For load_interval_length_hours:
    #     0.25: 96 entries for daily and 35040 for yearly
    #     0.5:  48 entries for daily and 17520 for yearly
    #     1.0:  24 entries for daily and 8760 for yearly
    default_load_watts_profile = config["default_load_watts"]
    default_gen_watts_profile = config["default_gen_watts"]
    default_load_var_profile = config["default_load_var"]
    default_gen_var_profile = config["default_gen_var"]

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
                        loadIntervalLengthHours=1.0,
                        defaultLoadWatts=default_load_watts_profile,
                        defaultGenWatts=default_gen_watts_profile,
                        defaultLoadVar=default_load_var_profile,
                        defaultGenVar=default_gen_var_profile,
                    ),
                    solve=HcSolveConfigInput(stepSizeMinutes=30),
                )
            ),
            work_package_name=config["work_package_name"],
        ))
        print_run(result)
    except Exception as e:
        print(e)

    await eas_client.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
