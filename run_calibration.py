import asyncio
import sys
from datetime import datetime

from zepben.eas import HcFeederScenarioAllocationStrategy, HcGeneratorConfigInput, \
    HcModelConfigInput, Mutation

from utils import get_client, get_config_dir, fetch_feeders, print_run

"""
Perform a calibration run which will utilise PQV data to model the network, and output voltage deltas between the PQV actuals and the
simulated network. Find more information on calibration at:
    https://zepben.github.io/evolve/docs/hosting-capacity-service/docs/next/how-to-guides/calibration#how-to-run

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

    # When providing a HcGeneratorConfigInput the following fields will be ignored or overridden during a calibration run:
    #   .model.calibration
    #   .model.meter_placement_config
    #   .solve.step_size_minutes
    #   .raw_results.

    # If transformer_tap_settings provided directly to async_run_hosting_capacity_calibration(), it will take
    # precedence over any 'transformer_tap_settings' supplied inside the generator_config parameter

    try:
        result = await eas_client.mutation(
            Mutation.run_calibration(
                calibration_name="<CALIBRATION_ID>",  # Any name - it will be stored alongside results.
                calibration_time_local=datetime(2025, month=7, day=12, hour=4, minute=0),
                # The time of the PQV data to model. Note this time must be present in EWBs load database.
                feeders=feeder_mrids,  # The feeders to model
                generator_config=HcGeneratorConfigInput(
                    # A customized GeneratorConfig can be passed to the calibration run.
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
                )
            )
        )
        print_run(result)
    except Exception as e:
        print(e)

    await eas_client.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
