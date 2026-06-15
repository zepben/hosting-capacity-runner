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
                initial_state_selector=IntrinsicInitialLoadStateConfigInput(
                    selector_mode=IntrinsicInitialStateSelectorMode.ZERO_LOAD,
                    start_time=datetime.fromisoformat(config["load_time"]["start1"]),
                ),
                constraints=IntrinsicConstraintsConfigInput(
                    voltage=IntrinsicVoltageConstraintsInput(
                        lv=IntrinsicLvVoltageConstraintInput(
                            max=253,
                            min=207
                        )
                    )
                ),
                injection_resource=IntrinsicInjectionResourceConfigInput(
                    method=IntrinsicInjectionResourceMethod.EXPORT_GENERATION,
                    load_model_type=IntrinsicLoadModelType.NEGATIVE_LOAD,
                    power_factor=0.95
                ),
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
