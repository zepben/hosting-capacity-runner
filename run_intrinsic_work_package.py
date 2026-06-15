"""
This script provides an example of how to run an Intrinsic Hosting Capacity work package.

Intrinsic mode inverts the standard hosting capacity question: instead of testing a specific DER scenario,
it finds how much additional load or generation the network can support before hitting a voltage or thermal limit.
"""

import asyncio
import sys
from datetime import datetime
from zepben.eas import Mutation, IntrinsicWorkPackageInput, IntrinsicSyfConfigInput, \
    IntrinsicSearchConfigInput, IntrinsicInitialLoadStateConfigInput, \
    IntrinsicInitialStateSelectorMode, IntrinsicConstraintsConfigInput, \
    IntrinsicVoltageConstraintsInput, IntrinsicLvVoltageConstraintInput, \
    IntrinsicInjectionResourceConfigInput, IntrinsicInjectionResourceMethod, IntrinsicLoadModelType

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
                # Initial state determines the baseline before generation is added.
                # ZERO_LOAD: empty network - theoretical upper bound, no existing load or DER.
                # FIXED_TIME: snapshot at a specific timestamp - requires start_time only.
                # PEAK_FEEDER_EXPORT: worst-case solar moment in a window - most conservative for solar HC.
                # PEAK_FEEDER_IMPORT: worst-case load moment - most conservative for EV/load growth.
                # FIXED_LOAD: uniform per-customer baseline - useful for standardised cross-feeder comparisons.
                initial_state_selector=IntrinsicInitialLoadStateConfigInput(
                    selector_mode=IntrinsicInitialStateSelectorMode.ZERO_LOAD,
                    start_time=datetime.fromisoformat(config["load_time"]["start1"]),
                ),
                # LV voltage limits in volts (phase-to-neutral).
                # Values here are emergency limits (VH2=260, VL2=207) - use normal limits (VH1=253, VL1=216)
                # for a more conservative assessment. Adjust to match your network standard.
                # Add hv= block to IntrinsicVoltageConstraintsInput to also enforce HV voltage limits (in per unit).
                # Add thermal= block to IntrinsicConstraintsConfigInput to enforce thermal limits.
                constraints=IntrinsicConstraintsConfigInput(
                    voltage=IntrinsicVoltageConstraintsInput(
                        lv=IntrinsicLvVoltageConstraintInput(
                            max=260,
                            min=207
                        )
                    )
                ),
                # EXPORT_GENERATION: find how much solar/generation the network can absorb.
                # Change to IMPORT_LOAD to find import headroom (e.g. for EV charging or load growth).
                injection_resource=IntrinsicInjectionResourceConfigInput(
                    method=IntrinsicInjectionResourceMethod.EXPORT_GENERATION,
                    load_model_type=IntrinsicLoadModelType.NEGATIVE_LOAD,
                    power_factor=0.95
                ),
                # step_kw_per_customer controls precision: smaller = finer results but more iterations.
                # If headroom equals step_kw_per_customer * max_steps the search hit the limit without
                # finding a constraint; increase max_steps or step size to find the true upper bound.
                search=IntrinsicSearchConfigInput(
                    step_kw_per_customer=1.0,
                    max_steps=200,
                    lock_out_capacity_zone_on_violation=True,
                    stop_on_hv_violation=True
                )
            ),
            config["work_package_name"]
        ))
        print_run(result)
    except Exception as e:
        print(e)

    await eas_client.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
