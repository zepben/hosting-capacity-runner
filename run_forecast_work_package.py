import asyncio
import sys
from datetime import datetime

from zepben.eas import ForecastConfig
from zepben.eas.client.work_package import (
    WorkPackageConfig,
    TimePeriod,
    ResultProcessorConfig,
    StoredResultsConfig,
    MetricsResultsConfig,
    WriterConfig,
    WriterOutputConfig,
    WriterType,
    EnhancedMetricsConfig,
    GeneratorConfig,
    ModelConfig,
    FeederScenarioAllocationStrategy,
    SolveConfig,
    RawResultsConfig,
    MeterPlacementConfig,
    SwitchMeterPlacementConfig,
    LoadPlacement,
    SolveMode,
)

from utils import get_client, get_config, print_run, get_config_dir

"""
This script provides an example of how to run a forecast work package for long term planning studies.
It allows you to configure a WorkPackage to run timeseries load flows for a given set of scenarios for a
configurable set of feeders.

Modify as needed for your environment.
"""


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    # -------------------------------------------------------------------------
    # ForecastConfig - defines the scope of the work package (SYF + time)
    # -------------------------------------------------------------------------
    # load_time reflects the base year (historical) load, and must correspond to data in your system.
    forecast_config = ForecastConfig(
        feeders=config["feeders"],
        years=config["forecast_years"],
        scenarios=config["scenarios"],
        load_time=TimePeriod(
            start_time=datetime.fromisoformat(config["load_time"]["start"]),
            end_time=datetime.fromisoformat(config["load_time"]["end"]),
        ),
    )

    # -------------------------------------------------------------------------
    # MeterPlacementConfig - controls where EnergyMeters are placed
    # -------------------------------------------------------------------------
    meter_placement_config = MeterPlacementConfig(
        feeder_head=True,
        dist_transformers=True,
        switch_meter_placement_configs=None,
    )

    # -------------------------------------------------------------------------
    # ModelConfig - controls how the power flow model is built
    # -------------------------------------------------------------------------
    model_config = ModelConfig(
        # --- Voltage limits for load/gen models (vm_pu is deprecated) ---
        load_vmin_pu=0.80,
        load_vmax_pu=1.15,
        gen_vmin_pu=0.70,
        gen_vmax_pu=2.00,

        # --- Load model ---
        load_model=1,
        load_placement=LoadPlacement.PER_USAGE_POINT,
        load_interval_length_hours=0.5,

        # --- Power factor settings ---
        p_factor_base_exports=-1,
        p_factor_base_imports=1,
        p_factor_forecast_pv=1,

        # --- Data fix: single phase loads ---
        fix_single_phase_loads=True,
        max_single_phase_load=30000.0,

        # --- Data fix: overloading consumers ---
        fix_overloading_consumers=True,
        max_load_tx_ratio=3.0,
        max_gen_tx_ratio=10.0,

        # --- Data fix: undersized service lines ---
        fix_undersized_service_lines=True,
        max_load_service_line_ratio=1.5,
        max_load_lv_line_ratio=2.0,

        # --- Network simplification ---
        simplify_network=True,
        collapse_negligible_impedances=True,
        combine_common_impedances=True,
        collapse_swer=True,
        collapse_lv_networks=True,

        # --- Emergency rating scaling ---
        emerg_amp_scaling=1.5,

        # --- Scenario allocation strategy ---
        feeder_scenario_allocation_strategy=FeederScenarioAllocationStrategy.ADDITIVE,

        # --- Voltage regulator settings ---
        closed_loop_v_reg_enabled=True,
        closed_loop_v_reg_replace_all=True,
        closed_loop_v_reg_set_point=0.985,
        closed_loop_v_band=2.0,
        closed_loop_time_delay=100,
        closed_loop_v_limit=1.1,

        # --- Default tap changer settings ---
        default_tap_changer_time_delay=100,
        default_tap_changer_set_point_pu=1.0,
        default_tap_changer_band=2.0,

        # --- Split phase settings ---
        split_phase_default_load_loss_percentage=0.4,
        split_phase_lv_kv=0.25,

        # --- SWER voltage mapping ---
        swer_voltage_to_line_voltage=[
            [230, 400],
            [240, 415],
            [250, 433],
            [6350, 11000],
            [6400, 11000],
            [12700, 22000],
            [19100, 33000],
        ],

        # --- Meter placement ---
        meter_placement_config=meter_placement_config,

        # --- Seed for reproducibility ---
        seed=123,
    )

    # -------------------------------------------------------------------------
    # SolveConfig - controls how the OpenDSS model is solved
    # -------------------------------------------------------------------------
    solve_config = SolveConfig(
        norm_vmin_pu=0.9,
        norm_vmax_pu=1.054,
        emerg_vmin_pu=0.8,
        emerg_vmax_pu=1.1,
        base_frequency=50,
        voltage_bases=[0.4, 0.433, 6.6, 11.0, 22.0, 33.0, 66.0, 132.0],
        max_iter=25,
        max_control_iter=20,
        mode=SolveMode.YEARLY,
        step_size_minutes=30.0,
    )

    # -------------------------------------------------------------------------
    # RawResultsConfig - controls what raw results OpenDSS produces
    # -------------------------------------------------------------------------
    raw_results_config = RawResultsConfig(
        energy_meter_voltages_raw=True,
        energy_meters_raw=True,
        results_per_meter=True,
        overloads_raw=True,
        voltage_exceptions_raw=True,
    )

    # -------------------------------------------------------------------------
    # EnhancedMetricsConfig - controls Network Performance Metrics Enhanced table
    # -------------------------------------------------------------------------
    enhanced_metrics_config = EnhancedMetricsConfig(
        populate_enhanced_metrics=True,
        populate_enhanced_metrics_profile=True,
        populate_duration_curves=True,
        populate_constraints=True,
        populate_weekly_reports=True,
        calculate_normal_for_load_thermal=True,
        calculate_emerg_for_load_thermal=True,
        calculate_normal_for_gen_thermal=True,
        calculate_emerg_for_gen_thermal=True,
        calculate_co2=True,
    )

    # -------------------------------------------------------------------------
    # StoredResultsConfig - controls which raw results are stored in the database
    # -------------------------------------------------------------------------
    stored_results_config = StoredResultsConfig(
        energy_meter_voltages_raw=False,
        energy_meters_raw=False,
        overloads_raw=False,
        voltage_exceptions_raw=False,
    )

    # -------------------------------------------------------------------------
    # ResultProcessorConfig
    # -------------------------------------------------------------------------
    result_processor_config = ResultProcessorConfig(
        writer_config=WriterConfig(
            writer_type=WriterType.POSTGRES,
            output_writer_config=WriterOutputConfig(
                enhanced_metrics_config=enhanced_metrics_config,
            ),
        ),
        stored_results=stored_results_config,
        metrics=MetricsResultsConfig(True),
    )

    # -------------------------------------------------------------------------
    # WorkPackageConfig - the top-level config
    # -------------------------------------------------------------------------
    work_package_config = WorkPackageConfig(
        name=config["work_package_name"],
        syf_config=forecast_config,
        generator_config=GeneratorConfig(
            model=model_config,
            solve=solve_config,
            raw_results=raw_results_config,
        ),
        result_processor_config=result_processor_config,
        quality_assurance_processing=False,
    )

    try:
        result = await eas_client.async_run_hosting_capacity_work_package(work_package_config)
        print_run(result)
    except Exception as e:
        import traceback
        traceback.print_exc()

    await eas_client.aclose()


if __name__ == "__main__":
    asyncio.run(main(sys.argv))