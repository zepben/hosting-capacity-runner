import asyncio
import sys
from datetime import datetime

from zepben.eas import ForecastConfig
from zepben.eas.client.work_package import WorkPackageConfig, TimePeriod, ResultProcessorConfig, StoredResultsConfig, \
    MetricsResultsConfig, WriterConfig, WriterOutputConfig, EnhancedMetricsConfig, GeneratorConfig, ModelConfig, \
    FeederScenarioAllocationStrategy, SolveConfig, RawResultsConfig, SwitchMeterPlacementConfig, SwitchClass, MeterPlacementConfig

from utils import get_client, get_config, print_run, get_config_dir

"""
This script provides an example of how to run a forecast work package for long term planning studies.
It allows you to configure a WorkPackage to run 10+ years of timeseries load flows for a given set of scenarios for a
configurable set of feeders.
"""


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    # Forecast Config example set up
    # This can be set up through the config file or by hard coding in the variables below.
    # The below will run a forecast-based work package for the configured feeders, years, and scenarios, over the time period specified in load_time below.
    # Note load_time reflects the base year (historical) load, and must be correctly specified to be a period of load data that exists in your system.
    # Consult your EWB HCM administrator if you do not know what load is available in your environment.
    forecast_config = ForecastConfig(
        feeders=config["feeders"],
        years=config["forecast_years"],
        scenarios=config["scenarios"],
        load_time=TimePeriod(
            start_time=datetime.fromisoformat(config["load_time"]["start1"]),
            end_time=datetime.fromisoformat(config["load_time"]["end1"]),
        )
    )

    result = await eas_client.async_run_hosting_capacity_work_package(
        WorkPackageConfig(
            name=config["work_package_name"],
            syf_config=forecast_config,
            generator_config=GeneratorConfig(
                model=ModelConfig(
                    meter_placement_config=MeterPlacementConfig(
                        switch_meter_placement_configs=[
                            SwitchMeterPlacementConfig(
                                meter_switch_class=SwitchClass.DISCONNECTOR,
                                name_pattern="LV Circuit Head.*"
                            ),
                            SwitchMeterPlacementConfig(
                                meter_switch_class=SwitchClass.FUSE,
                                name_pattern="LV Circuit Head.*"
                            )
                        ]
                    ),
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

                    closed_loop_v_reg_enabled=True,
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
