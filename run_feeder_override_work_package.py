import asyncio
import sys
from datetime import datetime

from zepben.eas import FeederConfigs, ForecastConfig, FixedTimeLoadOverride
from zepben.eas.client.work_package import WorkPackageConfig, TimePeriod, ResultProcessorConfig, StoredResultsConfig, \
    MetricsResultsConfig, WriterConfig, WriterOutputConfig, EnhancedMetricsConfig, GeneratorConfig, ModelConfig, \
    FeederScenarioAllocationStrategy, SolveConfig, RawResultsConfig, FeederConfig, TimePeriodLoadOverride, FixedTime

from utils import get_client, get_config, print_run, get_config_dir

"""
This script provides an example of how to run a work package with configuration for overriding the load data for specific 
loads in the feeders. This allows you to perform single timestep, fixed time studies for a feeder.
"""


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    # Feeder Configs example set up
    # More entries can be added into the configs list based on the config supplied (or hard coded)
    feeder_configs = FeederConfigs(
        configs=[
            # This configuration will run FEEDER_MRID_1 using the base (as built) model for a single timestep (time), while overriding the load for two specific
            # load IDs on that feeder.
            #
            # In practice these load_ids will be connection point identifiers and to understand what IDs you need # to use you will need to have an
            # understanding of how load data is keyed in your deployment. Contact your EWB HCM administrator if you have questions on how to configure this
            # for your environment.
            FeederConfig(
                feeder="<FEEDER_MRID_1>",
                years=[2025],   # Ignored as scenario is base.
                scenarios=["base"],
                load_time=FixedTime(
                    time=datetime.fromisoformat(config["load_time"]["start1"]),
                    # Override two loads load profiles.
                    # Note if these load ids don't exist in the feeder, this will have no effect so ensure this is mapped correctly.
                    load_overrides=
                    {
                        "<load_id1>": FixedTimeLoadOverride(
                            load_watts=[5000.0],
                            load_var=[50.0],
                            gen_var=None,
                            gen_watts=None
                        ),
                        "<load_id2>": FixedTimeLoadOverride(
                            load_watts=[5000.0],
                            load_var=[50.0],
                            gen_var=None,
                            gen_watts=None
                        ),
                    }
                )
            ),

            # This will cause FEEDER_MRID_2 to run, similar to above however with the override being applied to load_id3 being multiple timesteps.
            # This allows you to step-change the load for a single profile while keeping the rest of the load for the feeder consistent. A typical
            # scenario would be to ramp up the load on one customer on a feeder to see all these results in one work package.
            FeederConfig(
                feeder="<FEEDER_MRID_2>",
                years=config["forecast_years"],
                scenarios=config["scenarios"],
                load_time=FixedTime(
                    time=datetime.fromisoformat(config["load_time"]["start1"]),
                    load_overrides=
                    {"<load_id3>": FixedTimeLoadOverride(
                        # Fixed time load override supports any number of entries, however if an override is supplied it must be the same number of entries
                        # for all. In the below example, every list supplied must have exactly 3 entries.
                        load_watts=[10000.0, 20000.0, 30000.0],
                        load_var=[50.0, 100.0, 150.0],
                        gen_var=None,
                        gen_watts=None
                    )}
                )
            )
        ]
    )

    result = await eas_client.async_run_hosting_capacity_work_package(
        WorkPackageConfig(
            name=config["work_package_name"],
            syf_config=feeder_configs,
            generator_config=GeneratorConfig(
                model=ModelConfig(
                    vmax_pu=1.2,
                    vmin_pu=0.8,
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
                ),
                solve=SolveConfig(step_size_minutes=30.0),
                raw_results=RawResultsConfig(True, True, True, True, True)
            ),

            result_processor_config=ResultProcessorConfig(
                writer_config=WriterConfig(

                    output_writer_config=WriterOutputConfig(
                        enhanced_metrics_config=EnhancedMetricsConfig(
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                        ))),
                stored_results=StoredResultsConfig(True, True, True, True),
                metrics=MetricsResultsConfig(True)
            ),
            quality_assurance_processing=True
        )
    )

    print_run(result)
    await eas_client.aclose()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
