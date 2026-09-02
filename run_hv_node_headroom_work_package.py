"""
Example: run an HV Node Headroom work package.

HV counterpart to LV intrinsic: tests HV nodes one at a time to find headroom before a
voltage/thermal limit. Run time scales with node count. Full field reference: HCM docs,
"How to run an HV Node Headroom Work Package".
"""

import asyncio
import sys
from datetime import datetime

from zepben.eas import Mutation, HvNodeHeadroomWorkPackageInput, IntrinsicSyfConfigInput, \
    IntrinsicInitialLoadStateConfigInput, IntrinsicInitialStateSelectorMode, \
    IntrinsicConstraintsConfigInput, IntrinsicVoltageConstraintsInput, IntrinsicLvVoltageConstraintInput, \
    IntrinsicHvVoltageConstraintInput, IntrinsicThermalConstraintsInput, IntrinsicThermalConstraintInput, \
    IntrinsicRatingBasis, IntrinsicInjectionResourceConfigInput, IntrinsicInjectionResourceMethod, \
    IntrinsicLoadModelType, IntrinsicWriterConfigInput, HcWriterType, \
    HvNodeHeadroomSearchConfigInput, HvNodeLocationSelectorInput, HvNodeLocationKind

from utils import get_client, get_config, print_run, get_config_dir


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    try:
        result = await eas_client.mutation(Mutation.run_hv_node_headroom_work_package(
            HvNodeHeadroomWorkPackageInput(
                syf=IntrinsicSyfConfigInput(
                    feeders=config["feeders"],
                    scenario="base",  # or a different scenario if desired
                    year=config["forecast_years"][0]
                ),
                # Baseline before generation is added - see docs "Choosing the Initial State" for mode comparison.
                initialStateSelector=IntrinsicInitialLoadStateConfigInput(
                    selectorMode=IntrinsicInitialStateSelectorMode.ZERO_LOAD,
                    # Naive datetimes are interpreted in the server's timezone, not yours.
                    startTime=datetime.fromisoformat(config["load_time"]["start1"]),
                    # endTime=...,  # required for PEAK_FEEDER_EXPORT/PEAK_FEEDER_IMPORT
                    # includeLoads=True, includeExistingDer=True,             # FIXED_TIME/PEAK_FEEDER_EXPORT/PEAK_FEEDER_IMPORT only
                    # loadScalingFactor=1.0, derScalingFactor=1.0,           # FIXED_TIME/PEAK_FEEDER_EXPORT/PEAK_FEEDER_IMPORT only
                    # perCustomerLoadWatts=500.0, perCustomerGenWatts=0.0,   # FIXED_LOAD only, required
                    # perCustomerLoadVar=0.0, perCustomerGenVar=0.0,         # FIXED_LOAD only, required
                ),
                # HV node types to test. Default (selector omitted) is DTX_HV_TERMINAL only.
                nodeLocationSelector=HvNodeLocationSelectorInput(
                    locationKinds=[
                        HvNodeLocationKind.DTX_HV_TERMINAL,
                        HvNodeLocationKind.SWITCH_UPSTREAM_TERMINAL,
                        HvNodeLocationKind.LINE_TEE,
                    ]
                ),
                # LV voltage limits, volts phase-to-neutral. Adjust to your network standard.
                # A supplied hv=/thermal= block enables that constraint - see docs "Constraints Config".
                constraints=IntrinsicConstraintsConfigInput(
                    voltage=IntrinsicVoltageConstraintsInput(
                        lv=IntrinsicLvVoltageConstraintInput(max=260, min=207),
                        hv=IntrinsicHvVoltageConstraintInput(minPu=0.90, maxPu=1.1),
                    ),
                    thermal=IntrinsicThermalConstraintsInput(
                        lv=IntrinsicThermalConstraintInput(percentOfRating=100.0, ratingBasis=IntrinsicRatingBasis.NORMAL),
                        hv=IntrinsicThermalConstraintInput(percentOfRating=100.0, ratingBasis=IntrinsicRatingBasis.NORMAL),
                    ),
                ),
                # EXPORT_GENERATION: solar/gen headroom per node. IMPORT_LOAD: import headroom (EV/load growth).
                injectionResource=IntrinsicInjectionResourceConfigInput(
                    method=IntrinsicInjectionResourceMethod.EXPORT_GENERATION,
                    loadModelType=IntrinsicLoadModelType.NEGATIVE_LOAD,
                    powerFactor=0.95
                    # phaseMatching=...,  # only MATCH_CUSTOMER_PHASES exposed currently
                    # pvProfileId="some-pv-profile-id",  # required when loadModelType is PV_SYSTEM
                ),
                # headroom == stepKwPerNode * maxStepsPerNode means search hit the cap, not a
                # real constraint - raise maxStepsPerNode (<=1000) or step size.
                search=HvNodeHeadroomSearchConfigInput(
                    stepKwPerNode=10.0,
                    maxStepsPerNode=200,
                ),
                # PARQUET writes result files, POSTGRES writes to the results database - check which your environment supports.
                resultsWriter=IntrinsicWriterConfigInput(
                    writerType=HcWriterType.PARQUET,
                ),

                # solve= (HcSolveConfigInput) and model= (HcModelConfigInput) are also accepted here,
                # with the same fields as in run_forecast_work_package.py.
            ),
            config["work_package_name"]
        ))
        print_run(result)
    except Exception as e:
        print(e)

    await eas_client.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
