import asyncio
import sys
from datetime import datetime

from zepben.eas import ForecastConfigInput, TimePeriodInput, Mutation, WorkPackageInput, HcGeneratorConfigInput, HcModelConfigInput, HcFeederScenarioAllocationStrategy, HcSolveConfigInput, HcRawResultsConfigInput, HcResultProcessorConfigInput, HcWriterConfigInput, HcWriterOutputConfigInput, HcEnhancedMetricsConfigInput, HcStoredResultsConfigInput, HcMetricsResultsConfigInput

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
    forecast_config = ForecastConfigInput(
        feeders=config["feeders"],
        years=config["forecast_years"],
        scenarios=config["scenarios"],
        time_period=TimePeriodInput(
            start_time=datetime.fromisoformat(config["load_time"]["start"]).replace(tzinfo=None),
            end_time=datetime.fromisoformat(config["load_time"]["end"]).replace(tzinfo=None),
        )
    )

    try:
        result = await eas_client.mutation(Mutation.run_work_package(
            WorkPackageInput(
                forecast_config=forecast_config,
                generator_config=HcGeneratorConfigInput(
                    model=HcModelConfigInput(
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
                        feeder_scenario_allocation_strategy=HcFeederScenarioAllocationStrategy.ADDITIVE,
                        closed_loop_v_reg_enabled=False,
                        closed_loop_v_reg_set_point=0.9925,
                        seed=123,
                    ),
                    solve=HcSolveConfigInput(step_size_minutes=30.0),
                    raw_results=HcRawResultsConfigInput(
                        energy_meter_voltages_raw=True,
                        energy_meters_raw=True,
                        overloads_raw=True,
                        results_per_meter=True,
                        voltage_exceptions_raw=True,
                    )
                ),

                result_processor_config=HcResultProcessorConfigInput(
                    writer_config=HcWriterConfigInput(
                        output_writer_config=HcWriterOutputConfigInput(
                            enhanced_metrics_config=HcEnhancedMetricsConfigInput(
                                calculate_co_2=False,
                                calculate_emerg_for_gen_thermal=True,
                                calculate_emerg_for_load_thermal=True,
                                calculate_normal_for_gen_thermal=True,
                                calculate_normal_for_load_thermal=True,
                                populate_constraints=False,
                                populate_duration_curves=True,
                                populate_enhanced_metrics=True,
                                populate_enhanced_metrics_profile=False,
                                populate_weekly_reports=False,
                            ))),
                    stored_results=HcStoredResultsConfigInput(
                        energy_meter_voltages_raw=False,
                        energy_meters_raw=False,
                        overloads_raw=False,
                        voltage_exceptions_raw=False,
                    ),
                    metrics=HcMetricsResultsConfigInput(calculate_performance_metrics=False)
                ),
                quality_assurance_processing=False
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
