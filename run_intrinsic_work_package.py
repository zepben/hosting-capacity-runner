"""
Example: run an Intrinsic Hosting Capacity work package.

Finds how much load/generation the network can support before hitting a voltage/thermal limit,
instead of testing a specific DER scenario. Full field reference: HCM docs, "How to run a
Hosting Capacity Work Package".
"""

import asyncio
import sys
from datetime import datetime
from zepben.eas import Mutation, IntrinsicWorkPackageInput, IntrinsicSyfConfigInput, \
    IntrinsicSearchConfigInput, IntrinsicInitialLoadStateConfigInput, \
    IntrinsicInitialStateSelectorMode, IntrinsicConstraintsConfigInput, \
    IntrinsicVoltageConstraintsInput, IntrinsicLvVoltageConstraintInput, IntrinsicHvVoltageConstraintInput, \
    IntrinsicThermalConstraintsInput, IntrinsicThermalConstraintInput, IntrinsicRatingBasis, \
    IntrinsicInjectionResourceConfigInput, IntrinsicInjectionResourceMethod, IntrinsicLoadModelType, \
    IntrinsicPhaseMatching, IntrinsicAllocationConfigInput, IntrinsicAllocationMethod, \
    IntrinsicAllocationScope, IntrinsicExistingCapacityBasis, IntrinsicCapacityGroupPlacementType, \
    IntrinsicWriterConfigInput, HcWriterType, HcModelConfigInput, HcSolveConfigInput

from utils import get_client, get_config, print_run, get_config_dir


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    try:
        result = await eas_client.mutation(Mutation.run_intrinsic_work_package(
            IntrinsicWorkPackageInput(
                syf=IntrinsicSyfConfigInput(
                    feeders=config["feeders"],
                    scenario="base",
                    year=config["forecast_years"][0]
                ),
                # Baseline before generation is added - see docs "Choosing the Initial State" for
                # mode comparison.
                initial_state_selector=IntrinsicInitialLoadStateConfigInput(
                    selector_mode=IntrinsicInitialStateSelectorMode.ZERO_LOAD,
                    start_time=datetime.fromisoformat(config["load_time"]["start1"]),
                    # end_time=...,  # required for PEAK_FEEDER_EXPORT/PEAK_FEEDER_IMPORT
                    # include_loads=True, include_existing_der=True,          # FIXED_TIME/PEAK_FEEDER_EXPORT/PEAK_FEEDER_IMPORT only
                    # load_scaling_factor=1.0, der_scaling_factor=1.0,        # FIXED_TIME/PEAK_FEEDER_EXPORT/PEAK_FEEDER_IMPORT only
                    # per_customer_load_watts=500.0, per_customer_gen_watts=0.0,  # FIXED_LOAD only, required
                    # per_customer_load_var=0.0, per_customer_gen_var=0.0,        # FIXED_LOAD only, required
                ),
                # LV voltage limits, volts phase-to-neutral. Adjust to your network standard.
                # A supplied hv=/thermal= block enables that constraint - see docs "Constraints Config".
                constraints=IntrinsicConstraintsConfigInput(
                    voltage=IntrinsicVoltageConstraintsInput(
                        lv=IntrinsicLvVoltageConstraintInput(max=260, min=207),
                        hv=IntrinsicHvVoltageConstraintInput(min_pu=0.90, max_pu=1.10),
                    ),
                    thermal=IntrinsicThermalConstraintsInput(
                        lv=IntrinsicThermalConstraintInput(percent_of_rating=100.0, rating_basis=IntrinsicRatingBasis.NORMAL),
                        hv=IntrinsicThermalConstraintInput(percent_of_rating=100.0, rating_basis=IntrinsicRatingBasis.NORMAL),
                    ),
                ),
                # EXPORT_GENERATION: solar/gen headroom. IMPORT_LOAD: import headroom (EV/load growth).
                injection_resource=IntrinsicInjectionResourceConfigInput(
                    method=IntrinsicInjectionResourceMethod.EXPORT_GENERATION,
                    load_model_type=IntrinsicLoadModelType.NEGATIVE_LOAD,
                    power_factor=0.95
                    # phase_matching=...,  # only MATCH_CUSTOMER_PHASES exposed currently
                    # pv_profile_id="some-pv-profile-id",  # required when load_model_type is PV_SYSTEM
                ),
                # headroom == step_kw_per_customer * max_steps means search hit the cap, not a real
                # constraint - raise max_steps (<=10000) or step size.
                search=IntrinsicSearchConfigInput(
                    step_kw_per_customer=1.0,
                    max_steps=200,
                    lock_out_capacity_zone_on_violation=True,
                    stop_on_hv_violation=True
                ),

                # for the solve, model and results_writer configs, see run_forecast_work_package.py, and you can copy paste it directly in here.
            ),
            config["work_package_name"]
        ))
        print_run(result)
    except Exception as e:
        print(e)

    await eas_client.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
