import asyncio
import copy
import sys
from datetime import datetime

from zepben.eas import WorkPackageInput, HcGeneratorConfigInput, HcModelConfigInput, HcFeederScenarioAllocationStrategy, HcSolveConfigInput, \
    HcRawResultsConfigInput, FeederConfigsInput, FeederConfigInput, TimePeriodInput, HcResultProcessorConfigInput, HcWriterConfigInput, \
    HcWriterOutputConfigInput, HcEnhancedMetricsConfigInput, HcStoredResultsConfigInput, HcMetricsResultsConfigInput, Mutation, Query, InterventionConfigInput, \
    YearRangeInput, InterventionClass, CandidateGenerationConfigInput, CandidateGenerationType

from utils import get_client, get_config, print_run, get_config_dir, print_progress

"""
This script provides an example of how to run an intervention work package for long term planning studies.
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
    forecast_config = FeederConfigsInput(
        configs=[
            FeederConfigInput(
                feeder=config["feeders"],
                years=config["forecast_years"],
                scenarios=config["scenarios"],
                time_period=TimePeriodInput(
                    start_time=datetime.fromisoformat(config["load_time"]["start1"]),
                    end_time=datetime.fromisoformat(config["load_time"]["end1"])
                )
            )
        ]
    )

    base_work_package_config = WorkPackageInput(
        feeder_configs=forecast_config,
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
            solve=HcSolveConfigInput(step_size_minutes=30),
            raw_results=HcRawResultsConfigInput(
                energy_meter_voltages_raw=True,
                energy_meters_raw=True,
                overloads_raw=True,
                results_per_meter=True,
                voltage_exceptions_raw=True
            )
        ),
        result_processor_config=HcResultProcessorConfigInput(
            writer_config=HcWriterConfigInput(
                output_writer_config=HcWriterOutputConfigInput(
                    enhanced_metrics_config=HcEnhancedMetricsConfigInput(
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
                    )
                )
            ),
            stored_results=HcStoredResultsConfigInput(
                energy_meter_voltages_raw=False,
                energy_meters_raw=False,
                overloads_raw=True,
                voltage_exceptions_raw=False
            ),
            metrics=HcMetricsResultsConfigInput(calculate_performance_metrics=True)
        ),
        quality_assurance_processing=True
    )

    try:
        # ==== IF STARTING FROM SCRATCH ====
        # start base work package
        print(f"Sending base work package with config: {base_work_package_config}")
        result = await eas_client.mutation(Mutation.run_work_package(base_work_package_config, config["work_package_name"]))
        print_run(result)
        if "data" not in result:
            return
        base_work_package_id = result["data"]["runWorkPackage"]

        # wait for work package to finish
        while True:
            result = await eas_client.query(Query.get_active_work_packages())
            print_progress(result)
            if "data" not in result:
                return
            work_packages_progress = result["data"]["getWorkPackageProgress"]
            unfinished_work_package_ids = (
                work_packages_progress["pending"] +
                [progress["id"] for progress in work_packages_progress["inProgress"]]
            )
            if base_work_package_id not in unfinished_work_package_ids:
                break
            await asyncio.sleep(5)

        # ==== ELSE ====
        # base_work_package_id = "ID-OF-PREVIOUSLY-RAN-WORK-PACKAGE"
        # ==== END ====

        # start intervention work package
        intervention_config = InterventionConfigInput(
            base_work_package_id=base_work_package_id,
            year_range=YearRangeInput(
                min_year=2026,
                max_year=2030
            ),
            allocation_limit_per_year=100,
            intervention_type=InterventionClass.COMMUNITY_BESS,
            candidate_generation=CandidateGenerationConfigInput(
                type=CandidateGenerationType.CRITERIA,
                intervention_criteria_name="threshold_set_1"
            ),
            allocation_criteria="bess_allocation_criteria_1",
            specific_allocation_instance="bess_instance_1"
        )
        intervention_work_package_config = copy.copy(base_work_package_config)  # shallow copy
        intervention_work_package_config.intervention = intervention_config
        print(f"Sending intervention work package with config: {intervention_work_package_config}")
        result = await eas_client.mutation(Mutation.run_work_package(intervention_work_package_config, config["work_package_name"]))
        print_run(result)

    except Exception as e:
        print(e)

    await eas_client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
