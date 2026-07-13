"""
This script provides an example of how to run an Intervention work package.

An intervention work package is a normal forecast work package with an additional `intervention`
block set, pointing `baseWorkPackageId` at a prior work package. That base work
package must have been run with: EnhancedMetrics=True, distTransformers=True,
ScenarioAllocationStrategy=ADDITIVE, and either a single year, or a contiguous range of years

See the "How to run an Intervention Work Package" guide in the HCS documentation for details

Set INTERVENTION_TYPE below to choose which intervention to run. 

Note: `specificAllocationInstance` (single instance name) is used below for COMMUNITY_BESS,
LV_STATCOMS, and DISTRIBUTION_TX_OLTC. An upcoming release replaces this with
`allocationInstanceSelection` (a list of instance names), which will let COMMUNITY_BESS size
across multiple candidate instances instead of just one. Update these examples once that ships.
"""

import asyncio
import sys
from datetime import datetime
from zepben.eas import ForecastConfigInput, TimePeriodInput, Mutation, WorkPackageInput, HcGeneratorConfigInput, \
    HcModelConfigInput, HcFeederScenarioAllocationStrategy, HcSolveConfigInput, HcMeterPlacementConfigInput, \
    HcResultProcessorConfigInput, HcWriterConfigInput, HcWriterOutputConfigInput, HcEnhancedMetricsConfigInput, \
    HcStoredResultsConfigInput, HcMetricsResultsConfigInput, \
    InterventionConfigInput, InterventionClass, YearRangeInput, DvmsConfigInput, DvmsRegulatorConfigInput, \
    PhaseRebalanceProportionsInput, CandidateGenerationConfigInput, CandidateGenerationType
from utils import get_client, get_config, print_run, get_config_dir

# Choose which intervention to run.
INTERVENTION_TYPE = InterventionClass.COMMUNITY_BESS

# Work package ID of the base (non-intervention) work package to compare against.
BASE_WORK_PACKAGE_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Year range for the intervention. Must be a single year or a contiguous range, and should match the base work package's years.
YEAR_RANGE = YearRangeInput(minYear=2026, maxYear=2030)

# COMMUNITY_BESS
def build_community_bess_intervention() -> InterventionConfigInput:
    return InterventionConfigInput(
        baseWorkPackageId=BASE_WORK_PACKAGE_ID,
        yearRange=YEAR_RANGE,
        interventionType=InterventionClass.COMMUNITY_BESS,
        allocationLimitPerYear=20,  # Maximum number of batteries to install per year
        candidateGeneration=CandidateGenerationConfigInput(
            type=CandidateGenerationType.CRITERIA,  # Required for COMMUNITY_BESS
            interventionCriteriaName="bess-intervention-criteria-gen-thermal",  # References intervention_candidate_criteria.name
        ),
        allocationCriteria="bess_allocation_criteria",  # References bess_allocation_criteria.name
        specificAllocationInstance="EcoSTORE",  # Optional; omit to consider all instances in bess_instances
        sizingLookaheadYears=3,  # Optional, defaults to 1
    )

# LV_STATCOMS
def build_lv_statcoms_intervention() -> InterventionConfigInput:
    return InterventionConfigInput(
        baseWorkPackageId=BASE_WORK_PACKAGE_ID,
        yearRange=YEAR_RANGE,
        interventionType=InterventionClass.LV_STATCOMS,
        allocationLimitPerYear=20,  # Maximum number of LV STATCOMs to install per year
        candidateGeneration=CandidateGenerationConfigInput(
            type=CandidateGenerationType.CRITERIA,  # Required for LV_STATCOMS
            interventionCriteriaName="lvstatcom-intervention-criteria",  # References intervention_candidate_criteria.name
        ),
        allocationCriteria="lv_statcom_allocation_criteria_2",  # References lv_statcom_allocation_criteria.name
        specificAllocationInstance="lv_statcom_instance_1",  # Optional; if omitted, first matching instance is used
    )

# DISTRIBUTION_TAP_OPTIMIZATION
def build_distribution_tap_optimization_intervention() -> InterventionConfigInput:
    return InterventionConfigInput(
        baseWorkPackageId=BASE_WORK_PACKAGE_ID,
        yearRange=YEAR_RANGE,
        interventionType=InterventionClass.DISTRIBUTION_TAP_OPTIMIZATION,
        allocationLimitPerYear=30,  # Optional; omit for unlimited transformers per year
        candidateGeneration=CandidateGenerationConfigInput(
            type=CandidateGenerationType.TAP_OPTIMIZATION,  # Required for DISTRIBUTION_TAP_OPTIMIZATION
            # Voltage thresholds, applied per measurement zone per year
            averageVoltageSpreadThreshold=40,
            voltageUnderLimitHoursThreshold=48,
            voltageOverLimitHoursThreshold=48,
            # Tap weighting thresholds (direction arbitration); defaults (-10.0, 10.0) suit most cases
            tapWeightingFactorLowerThreshold=-10.0,
            tapWeightingFactorUpperThreshold=10.0,
        ),
    )

# DISTRIBUTION_TX_OLTC
def build_distribution_tx_oltc_intervention() -> InterventionConfigInput:
    return InterventionConfigInput(
        baseWorkPackageId=BASE_WORK_PACKAGE_ID,
        yearRange=YEAR_RANGE,
        interventionType=InterventionClass.DISTRIBUTION_TX_OLTC,
        allocationLimitPerYear=50,  # Maximum number of OLTCs to install per year
        candidateGeneration=CandidateGenerationConfigInput(
            type=CandidateGenerationType.CRITERIA,  # Required for DISTRIBUTION_TX_OLTC
            interventionCriteriaName="threshold_set_2",  # References intervention_candidate_criteria.name
        ),
        allocationCriteria="distribution_transformer_oltc_allocation_criteria_1",  # References distribution_transformer_oltc_allocation_criteria.name
        specificAllocationInstance="distribution_transformer_oltc_instance_1",  # Optional; only 1 instance allowed
    )

# TARIFF_REFORM
def build_tariff_reform_intervention() -> InterventionConfigInput:
    return InterventionConfigInput(
        baseWorkPackageId=BASE_WORK_PACKAGE_ID,
        yearRange=YEAR_RANGE,
        interventionType=InterventionClass.TARIFF_REFORM,  # or InterventionClass.CONTROLLED_LOAD_HOT_WATER
        allocationCriteria="load_reshape_strategy_1",  # References criteria_name in load_reshape_strategies
    )

# DVMS
def build_dvms_intervention() -> InterventionConfigInput:
    return InterventionConfigInput(
        baseWorkPackageId=BASE_WORK_PACKAGE_ID,
        yearRange=YEAR_RANGE,
        interventionType=InterventionClass.DVMS,
        dvms=DvmsConfigInput(
            lowerLimit=0.9,             # Minimum acceptable voltage (per unit)
            upperLimit=1.1,             # Maximum acceptable voltage (per unit)
            lowerPercentile=5,          # Lower percentile of customer voltages to consider
            upperPercentile=95,         # Upper percentile of customer voltages to consider
            maxIterations=3,            # Maximum tap adjustment attempts per time step
            regulatorConfig=DvmsRegulatorConfigInput(
                puTarget=1.0,                 # Target voltage (per unit)
                puDeadbandPercent=12,         # Deadband width as % of target
                maxTapChangePerStep=2,        # Maximum tap positions to change per iteration
                allowPushToLimit=True,        # Allow tap changes that improve one side of the voltage distribution even if worsening the other
            ),
        ),
    )

# PHASE_REBALANCING
def build_phase_rebalancing_intervention() -> InterventionConfigInput:
    return InterventionConfigInput(
        baseWorkPackageId=BASE_WORK_PACKAGE_ID,
        yearRange=YEAR_RANGE,
        interventionType=InterventionClass.PHASE_REBALANCING,
        phaseRebalanceProportions=PhaseRebalanceProportionsInput(
            a=1,  # Target proportions for redistributing single-phase customers across phases.
            b=1,  # Values do not need to sum to 1 (they are normalized internally), but must
            c=1,  # all be non-negative. a=b=c=1 gives an even distribution.
        ),
    )


INTERVENTION_BUILDERS = {
    InterventionClass.COMMUNITY_BESS: build_community_bess_intervention,
    InterventionClass.LV_STATCOMS: build_lv_statcoms_intervention,
    InterventionClass.DISTRIBUTION_TAP_OPTIMIZATION: build_distribution_tap_optimization_intervention,
    InterventionClass.DISTRIBUTION_TX_OLTC: build_distribution_tx_oltc_intervention,
    InterventionClass.TARIFF_REFORM: build_tariff_reform_intervention,
    InterventionClass.CONTROLLED_LOAD_HOT_WATER: build_tariff_reform_intervention,
    InterventionClass.DVMS: build_dvms_intervention,
    InterventionClass.PHASE_REBALANCING: build_phase_rebalancing_intervention,
}


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    # Forecast Config example set up.
    # This should match the base work package's configuration (feeders, years, scenarios, load
    # time period, model parameters, etc.) other than the intervention block itself, so that any
    # difference in results can only be attributed to the intervention.
    forecast_config = ForecastConfigInput(
        feeders=config["feeders"],
        years=config["forecast_years"],
        scenarios=config["scenarios"],
        timePeriod=TimePeriodInput(
            startTime=datetime.fromisoformat(config["load_time"]["start1"]),
            endTime=datetime.fromisoformat(config["load_time"]["end1"]),
        )
    )

    intervention_config = INTERVENTION_BUILDERS[INTERVENTION_TYPE]()

    try:
        result = await eas_client.mutation(Mutation.run_work_package(
            WorkPackageInput(
                forecastConfig=forecast_config,
                generatorConfig=HcGeneratorConfigInput(
                    model=HcModelConfigInput(
                        loadVMaxPu=1.2,
                        loadVMinPu=0.8,
                        pFactorBaseExports=-1,
                        pFactorBaseImports=1,
                        pFactorForecastPv=1,
                        fixSinglePhaseLoads=False,
                        maxSinglePhaseLoad=15000.0,
                        maxLoadServiceLineRatio=1.5,
                        maxLoadLvLineRatio=2.0,
                        maxLoadTxRatio=3.0,
                        maxGenTxRatio=10.0,
                        fixOverloadingConsumers=True,
                        fixUndersizedServiceLines=True,
                        # Must be ADDITIVE (the default) - candidate-based interventions will fail to build otherwise.
                        feederScenarioAllocationStrategy=HcFeederScenarioAllocationStrategy.ADDITIVE,
                        closedLoopVRegEnabled=False,
                        seed=123,
                        # Measurement zones must be set at the distribution transformer level for
                        # candidate-based interventions and NOT set at the Switch / LV feeder level.
                        meterPlacementConfig=HcMeterPlacementConfigInput(
                            feederHead=True,
                            distTransformers=True,
                        ),
                    ),
                    solve=HcSolveConfigInput(stepSizeMinutes=30),
                ),

                resultProcessorConfig=HcResultProcessorConfigInput(
                    writerConfig=HcWriterConfigInput(
                        outputWriterConfig=HcWriterOutputConfigInput(
                            enhancedMetricsConfig=HcEnhancedMetricsConfigInput(
                                populateEnhancedMetrics=True,
                                populateEnhancedMetricsProfile=False,
                                calculateEmergForLoadThermal=True,
                                calculateNormalForLoadThermal=True,
                                calculateCO2=True,
                                populateConstraints=False,
                                populateWeeklyReports=False,
                                populateDurationCurves=False,
                                calculateEmergForGenThermal=True,
                                calculateNormalForGenThermal=True,
                            ))),
                    # Caution: storing raw results uses significant storage - avoid for large work packages.
                    storedResults=HcStoredResultsConfigInput(
                        voltageExceptionsRaw=False,
                        overloadsRaw=False,
                        energyMetersRaw=False,
                        energyMeterVoltagesRaw=False
                    ),
                    # calculatePerformanceMetrics is deprecated - prefer populateEnhancedMetrics above.
                    metrics=HcMetricsResultsConfigInput(calculatePerformanceMetrics=False)
                ),
                qualityAssuranceProcessing=False,
                intervention=intervention_config,
            ),
            work_package_name=config["work_package_name"],
        ))
        print_run(result)
    except Exception as e:
        print(e)

    await eas_client.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
