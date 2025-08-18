import asyncio
import sys
from datetime import datetime

from zepben.eas import ForecastConfig
from zepben.eas.client.work_package import WorkPackageConfig, TimePeriod, ResultProcessorConfig, StoredResultsConfig, \
    MetricsResultsConfig, WriterConfig, WriterOutputConfig, EnhancedMetricsConfig, GeneratorConfig, ModelConfig, \
    FeederScenarioAllocationStrategy, SolveConfig, RawResultsConfig

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
    forecast_config = ForecastConfig(
        feeders=config["feeders"],
        years=config["forecast_years"],
        scenarios=config["scenarios"],
        load_time=TimePeriod(
            start_time=datetime.fromisoformat(config["load_time"]["start1"]),
            end_time=datetime.fromisoformat(config["load_time"]["end1"]),
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

    result = await eas_client.async_run_hosting_capacity_work_package(
        WorkPackageConfig(
            name=config["work_package_name"],
            syf_config=forecast_config,
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
                    load_interval_length_hours = 1.0,
                    default_load_watts=default_load_watts_profile,
                    default_gen_watts=default_gen_watts_profile,
                    default_load_var=default_load_var_profile,
                    default_gen_var=default_gen_var_profile,
                ),
                solve=SolveConfig(step_size_minutes=30.0),
                raw_results=RawResultsConfig(True, True, True, True, True)
            ),

            result_processor_config=ResultProcessorConfig(
                writer_config=WriterConfig(
                    output_writer_config=WriterOutputConfig(
                        enhanced_metrics_config=EnhancedMetricsConfig(
                            True,
                            False,
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                        ))),
                stored_results=StoredResultsConfig(False, False, True, False),
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
