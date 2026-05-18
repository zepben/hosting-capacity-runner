import asyncio
import sys
from datetime import datetime
from zepben.eas import Mutation, IntrinsicWorkPackageInput, IntrinsicSyfConfigInput, IntrinsicAllocationConfigInput, \
    IntrinsicSearchConfigInput, IntrinsicCapacityGroupPlacementType, IntrinsicInitialLoadStateConfigInput, \
    HcModelConfigInput, IntrinsicWriterConfigInput, IntrinsicInitialStateSelectorMode, IntrinsicConstraintsConfigInput, \
    IntrinsicThermalConstraintsInput, IntrinsicVoltageConstraintsInput, IntrinsicLvVoltageConstraintInput, \
    IntrinsicInjectionResourceConfigInput,IntrinsicInjectionResourceMethod,IntrinsicLoadModelType

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

    try:
        result = await eas_client.mutation(Mutation.run_intrinsic_work_package(
            IntrinsicWorkPackageInput(
                syfConfig=IntrinsicSyfConfigInput(
                    feeders=config["feeders"],
                    scenarios=["base"],
                    years=config["years"]
                ),
                initialStateSelectorConfig=IntrinsicInitialLoadStateConfigInput(
                    selectorMode=IntrinsicInitialStateSelectorMode.ZERO_LOAD,
                    startTime=datetime.fromisoformat(config["load_time"]["start1"])
                ),
                constraintsConfig=IntrinsicConstraintsConfigInput(
                  voltage=IntrinsicVoltageConstraintsInput(
                      lv=IntrinsicLvVoltageConstraintInput(
                          max=270,
                          min=207
                      )
                  )
                ),
                injectionResourceConfig=IntrinsicInjectionResourceConfigInput(
                    method=IntrinsicInjectionResourceMethod.IMPORT_LOAD,
                    loadModelType=IntrinsicLoadModelType.NEGATIVE_LOAD,
                    powerFactor=0.8
                ),
                searchConfig=IntrinsicSearchConfigInput(
                    stepKwPerCustomer=2.0,
                    maxSteps=200,
                    lockOutCapacityZoneOnViolation=True,
                    stopOnHvViolation=True
                )
            ),
            "test_intrinsic_work_package"
        ))
        print_run(result)
    except Exception as e:
        print(e)

    await eas_client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
