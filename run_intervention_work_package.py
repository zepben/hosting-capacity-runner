import asyncio
import sys
from datetime import datetime

from zepben.eas import ForecastConfigInput, TimePeriodInput, Mutation, WorkPackageInput, HcGeneratorConfigInput, HcModelConfigInput, HcFeederScenarioAllocationStrategy, HcSolveConfigInput, HcRawResultsConfigInput, HcResultProcessorConfigInput, HcWriterConfigInput, HcWriterOutputConfigInput, HcEnhancedMetricsConfigInput, HcStoredResultsConfigInput, HcMetricsResultsConfigInput, InterventionConfigInput, InterventionClass, YearRangeInput, CandidateGenerationConfigInput, CandidateGenerationType, DvmsConfigInput, DvmsRegulatorConfigInput, PhaseRebalanceProportionsInput

from utils import get_client, get_config, print_run, get_config_dir

"""
Runs an intervention work package using the same settings as the base forecast run.

Workflow:
  1. Run run_forecast_work_package.py and note the returned work package ID.
  2. Review the results and confirm you are happy with the base run.
  3. Set config["intervention"]["base_work_package_id"] to that ID.
  4. Set config["intervention"]["intervention_type"] to the desired type.
  5. Fill in the relevant config fields for that type (see below), then run this script.

Required config fields per intervention type:
  COMMUNITY_BESS             candidate_criteria, allocation_criteria, year_range
                             Optional: specific_allocation_instance, allocation_limit_per_year
  LV_STATCOMS                candidate_criteria, allocation_criteria, year_range
                             Optional: specific_allocation_instance, allocation_limit_per_year
  DISTRIBUTION_TX_OLTC       candidate_criteria, allocation_criteria, year_range
                             Optional: specific_allocation_instance, allocation_limit_per_year
  DISTRIBUTION_TAP_OPTIMIZATION  tap_optimization, year_range
                             Optional: allocation_limit_per_year
  TARIFF_REFORM              allocation_criteria
  CONTROLLED_LOAD_HOT_WATER  allocation_criteria
  DVMS                       dvms, year_range
  PHASE_REBALANCING          phase_rebalance_proportions, year_range
"""


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    forecast_config = ForecastConfigInput(
        feeders=config["feeders"],
        years=config["forecast_years"],
        scenarios=config["scenarios"],
        time_period=TimePeriodInput(
            start_time=datetime.fromisoformat(config["load_time"]["start"]).replace(tzinfo=None),
            end_time=datetime.fromisoformat(config["load_time"]["end"]).replace(tzinfo=None),
        )
    )

    ic = config["intervention"]
    intervention_type = InterventionClass[ic["intervention_type"]]
    tc = ic[ic["intervention_type"]]  # type-specific config block

    # CRITERIA type: COMMUNITY_BESS, LV_STATCOMS, DISTRIBUTION_TX_OLTC
    # TAP_OPTIMIZATION type: DISTRIBUTION_TAP_OPTIMIZATION
    # All others (TARIFF_REFORM, CONTROLLED_LOAD_HOT_WATER, DVMS, PHASE_REBALANCING): omit
    candidate_generation = None
    if tc.get("candidate_criteria"):
        candidate_generation = CandidateGenerationConfigInput(
            type_=CandidateGenerationType.CRITERIA,
            intervention_criteria_name=tc["candidate_criteria"],
        )
    elif intervention_type == InterventionClass.DISTRIBUTION_TAP_OPTIMIZATION:
        candidate_generation = CandidateGenerationConfigInput(
            type_=CandidateGenerationType.TAP_OPTIMIZATION,
            average_voltage_spread_threshold=tc.get("average_voltage_spread_threshold"),
            voltage_under_limit_hours_threshold=tc.get("voltage_under_limit_hours_threshold"),
            voltage_over_limit_hours_threshold=tc.get("voltage_over_limit_hours_threshold"),
            tap_weighting_factor_lower_threshold=tc.get("tap_weighting_factor_lower_threshold"),
            tap_weighting_factor_upper_threshold=tc.get("tap_weighting_factor_upper_threshold"),
        )

    dvms_config = None
    if intervention_type == InterventionClass.DVMS:
        r = tc["regulator_config"]
        dvms_config = DvmsConfigInput(
            lower_limit=tc["lower_limit"],
            upper_limit=tc["upper_limit"],
            lower_percentile=tc["lower_percentile"],
            upper_percentile=tc["upper_percentile"],
            max_iterations=tc["max_iterations"],
            regulator_config=DvmsRegulatorConfigInput(
                pu_target=r["pu_target"],
                pu_deadband_percent=r["pu_deadband_percent"],
                max_tap_change_per_step=r["max_tap_change_per_step"],
                allow_push_to_limit=r["allow_push_to_limit"],
            )
        )

    phase_rebalance_proportions = None
    if intervention_type == InterventionClass.PHASE_REBALANCING:
        phase_rebalance_proportions = PhaseRebalanceProportionsInput(
            a=tc["a"], b=tc["b"], c=tc["c"]
        )

    intervention_config = InterventionConfigInput(
        base_work_package_id=ic["base_work_package_id"],
        intervention_type=intervention_type,
        allocation_limit_per_year=tc.get("allocation_limit_per_year"),
        allocation_criteria=tc.get("allocation_criteria"),
        specific_allocation_instance=tc.get("specific_allocation_instance"),
        candidate_generation=candidate_generation,
        year_range=YearRangeInput(
            min_year=ic["year_range"]["min_year"],
            max_year=ic["year_range"]["max_year"],
        ) if ic.get("year_range") else None,
        dvms=dvms_config,
        phase_rebalance_proportions=phase_rebalance_proportions,
    )

    try:
        result = await eas_client.mutation(Mutation.run_work_package(
            WorkPackageInput(
                forecast_config=forecast_config,
                intervention=intervention_config,
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
