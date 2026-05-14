import asyncio
import sys
from datetime import datetime

from zepben.eas import Mutation, WorkPackageInput, HcGeneratorConfigInput, HcModelConfigInput, \
    HcFeederScenarioAllocationStrategy, HcResultProcessorConfigInput, HcWriterConfigInput, HcWriterOutputConfigInput, \
    HcEnhancedMetricsConfigInput, HcStoredResultsConfigInput, HcMetricsResultsConfigInput, FeederConfigsInput, \
    FeederConfigInput, FixedTimeInput, FixedTimeLoadOverrideInput

from utils import get_client, get_config, print_run, get_config_dir

"""
This script provides an example of how to run a work package with configuration for overriding the load data for specific
loads in the feeders. This allows you to perform single timestep, fixed time studies for a feeder.
Note overrides are experimental features, and this entails advanced usage of the HCM module.
Please contact Zepben to ensure you are creating an efficient and scalable solution with these features.
"""


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    # Feeder Configs example set up
    # More entries can be added into the configs list based on the config supplied (or hard coded)
    feeder_configs = FeederConfigsInput(
        configs=[
            # This configuration will run FEEDER_MRID_1 using the base (as built) model for a single timestep (time), while overriding the load for two specific
            # load IDs on that feeder.
            #
            # In practice these load_ids will be connection point identifiers and to understand what IDs you need # to use you will need to have an
            # understanding of how load data is keyed in your deployment. Contact your EWB HCM administrator if you have questions on how to configure this
            # for your environment.
            FeederConfigInput(
                feeder="<FEEDER_MRID_1>",
                years=[2025],  # Ignored as scenario is base.
                scenarios=["base"],
                fixedTime=FixedTimeInput(
                    loadTime=datetime.fromisoformat(config["load_time"]["start1"]),
                    # Override two loads load profiles.
                    # Note if these load ids don't exist in the feeder, this will have no effect so ensure this is mapped correctly.
                    overrides=
                    [
                        FixedTimeLoadOverrideInput(
                            loadId="<load_id1>",
                            loadWattsOverride=[5000.0],
                            loadVarOverride=[50.0],
                            genVarOverride=None,
                            genWattsOverride=None
                        ),
                        FixedTimeLoadOverrideInput(
                            loadId="<load_id1>",
                            loadWattsOverride=[5000.0],
                            loadVarOverride=[50.0],
                            genVarOverride=None,
                            genWattsOverride=None
                        ),
                    ]
                )
            ),

            # This will cause FEEDER_MRID_2 to run, similar to above however with the override being applied to load_id3 being multiple timesteps.
            # This allows you to step-change the load for a single profile while keeping the rest of the load for the feeder consistent. A typical
            # scenario would be to ramp up the load on one customer on a feeder to see all these results in one work package.
            FeederConfigInput(
                feeder="<FEEDER_MRID_2>",
                years=config["forecast_years"],
                scenarios=config["scenarios"],
                fixedTime=FixedTimeInput(
                    loadTime=datetime.fromisoformat(config["load_time"]["start1"]),
                    overrides=[
                        FixedTimeLoadOverrideInput(
                            loadId="<load_id3>",
                            # Fixed time load override supports any number of entries, however if an override is supplied it must be the same number of entries
                            # for all. In the below example, every list supplied must have exactly 3 entries.
                            loadWattsOverride=[10000.0, 20000.0, 30000.0],
                            loadVarOverride=[50.0, 100.0, 150.0],
                            genVarOverride=None,
                            genWattsOverride=None
                        )
                    ]
                )
            )
        ]
    )

    try:
        result = await  eas_client.mutation(Mutation.run_work_package(
            WorkPackageInput(
                feederConfigs=feeder_configs,
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
                    )
                ),
                resultProcessorConfig=HcResultProcessorConfigInput(
                    writerConfig=HcWriterConfigInput(

                        outputWriterConfig=HcWriterOutputConfigInput(
                            enhancedMetricsConfig=HcEnhancedMetricsConfigInput(
                                populateEnhancedMetrics=True,
                                populateEnhancedMetricsProfile=True,
                                calculateEmergForLoadThermal=True,
                                calculateNormalForLoadThermal=True,
                                calculateCO2=True,
                                populateConstraints=True,
                                populateWeeklyReports=True,
                                populateDurationCurves=True,
                                calculateEmergForGenThermal=True,
                                calculateNormalForGenThermal=True,
                            ))),
                    storedResults=HcStoredResultsConfigInput(
                        voltageExceptionsRaw=False,
                        overloadsRaw=True,
                        energyMetersRaw=False,
                        energyMeterVoltagesRaw=False
                    ),
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
