import asyncio
import sys
from datetime import datetime

from zepben.eas import GeneratorConfig, ModelConfig, FeederScenarioAllocationStrategy

from utils import get_client, get_config_dir, fetch_feeders

"""
Perform a calibration run which will utilise PQV data to model the network, and output voltage deltas between the PQV actuals and the
simulated network. Find more information on calibration at:
    https://zepben.github.io/evolve/docs/hosting-capacity-service/docs/next/how-to-guides/calibration#option-2-using-the-python-api

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

    # When providing a GeneratorConfig the following fields will be ignored or overridden during a calibration run:
    # GeneratorConfig.model.calibration
    # GeneratorConfig.model.meter_placement_config
    # GeneratorConfig.solve.step_size_minutes
    # GeneratorConfig.raw_results.

    # If transformer_tap_settings provided directly to async_run_hosting_capacity_calibration(), it will take
    # precedence over any 'transformer_tap_settings' supplied inside the generator_config parameter

    try:
        result = await eas_client.async_run_hosting_capacity_calibration(
            calibration_name="<CALIBRATION_ID>",  # Any name - it will be stored alongside results.
            calibration_time_local=datetime(2025, month=7, day=12, hour=4, minute=0),  # The time of the PQV data to model. Note this time must be present in EWBs load database.
            feeders=feeder_mrids,    # The feeders to model
            # transformer_tap_settings="<PREVIOUS_CALIBRATION_ID>", # The name of a set of previously generated tap settings that are to be applied before running the calibration work package.
            generator_config=GeneratorConfig(  # A customized GeneratorConfig can be passed to the calibration run.
                model=ModelConfig(
                    load_vmax_pu=1.2,
                    load_vmin_pu=0.8,
                    p_factor_base_exports=-1,
                    p_factor_base_imports=1,
                    p_factor_forecast_pv=1,
                    fix_single_phase_loads=False,
                    max_single_phase_load=15000.0,
                    max_load_service_line_ratio=1.0,
                    max_load_lv_line_ratio=2.0,
                    max_load_tx_ratio=2.0,
                    max_gen_tx_ratio=4.0,
                    fix_overloading_consumers=True,
                    fix_undersized_service_lines=True,
                    feeder_scenario_allocation_strategy=FeederScenarioAllocationStrategy.ADDITIVE,
                    closed_loop_v_reg_enabled=False,
                    closed_loop_v_reg_set_point=0.9925,
                    seed=123,
                )
            )
        )
        print(result)
    except Exception as e:
        print(e)

    await eas_client.aclose()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
