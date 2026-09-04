"""
Example: run a stacked Intervention work package.

A normal forecast work package with an `intervention` block set. The block combines up to one
candidate intervention with any of phaseRebalanceProportions, dvms and loadReshaping, all applied
to the same network. See HCS docs, "How to run an Intervention Work Package" for the base work
package prerequisites, "Interventions Options" for per-type parameters, and "Interventions
Concepts" for stacking vs chaining.

Remember to update the standard model config arguments at the bottom to match your parent work package.

Requires zepben.eas 2.18.0b1+.
"""

import asyncio
import sys
from datetime import datetime
from zepben.eas import ForecastConfigInput, TimePeriodInput, Mutation, WorkPackageInput, HcGeneratorConfigInput, \
    HcModelConfigInput, HcFeederScenarioAllocationStrategy, HcSolveConfigInput, HcMeterPlacementConfigInput, \
    HcResultProcessorConfigInput, HcWriterConfigInput, HcWriterOutputConfigInput, HcEnhancedMetricsConfigInput, \
    HcStoredResultsConfigInput, HcMetricsResultsConfigInput, \
    InterventionConfigInput, CandidateInterventionConfigInput, CandidateInterventionClass, \
    YearRangeInput, DvmsConfigInput, DvmsRegulatorConfigInput, PhaseRebalanceProportionsInput, \
    LoadReshapingConfigInput, CandidateGenerationConfigInput, CandidateGenerationType
from utils import get_client, get_config, print_run, get_config_dir

# The parent (previously called base) work package to compare against.
PARENT_WORK_PACKAGE_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Optional - if omitted, defaults to the work package's full year range.
YEAR_RANGE = YearRangeInput(minYear=1, maxYear=9999)

# --- Choose what to run -------------------------------------------------------------------------
# One candidate intervention, plus any combination of the three non-candidate ones.

# Set to None to run with no candidate intervention.
CANDIDATE_INTERVENTION = CandidateInterventionClass.COMMUNITY_BESS

ENABLE_LOAD_RESHAPING = True  # Previously called TARIFF_REFORM and CONTROLLED_LOAD_HOT_WATER
ENABLE_PHASE_REBALANCING = True
ENABLE_DVMS = False  # Runs at every time step (computationally expensive)


# --- Candidate interventions: pick AT MOST 1 --------------------------------------------------

def build_community_bess_candidate() -> CandidateInterventionConfigInput:
    return CandidateInterventionConfigInput(
        interventionType=CandidateInterventionClass.COMMUNITY_BESS,
        yearRange=YEAR_RANGE,
        allocationLimitPerYear=999,
        candidateGeneration=CandidateGenerationConfigInput(
            type=CandidateGenerationType.CRITERIA,
            interventionCriteriaName="<your-candidate-criteria>",  # intervention_candidate_criteria.name
            sizingLookaheadYears=3,
        ),
        candidateAllocationCriteria="<your-allocation-criteria>",  # bess_allocation_criteria.name
        allocationInstanceSelection=["<your-bess-instance>"],  # bess_instances.name; omit to size across all
    )


def build_lv_statcoms_candidate() -> CandidateInterventionConfigInput:
    return CandidateInterventionConfigInput(
        interventionType=CandidateInterventionClass.LV_STATCOMS,
        yearRange=YEAR_RANGE,
        allocationLimitPerYear=999,
        candidateGeneration=CandidateGenerationConfigInput(
            type=CandidateGenerationType.CRITERIA,
            interventionCriteriaName="<your-candidate-criteria>",  # intervention_candidate_criteria.name
        ),
        candidateAllocationCriteria="<your-allocation-criteria>",  # lv_statcom_allocation_criteria.name
        allocationInstanceSelection=["<your-statcom-instance>"],  # lv_statcom_instances.name
    )


def build_distribution_tap_optimization_candidate() -> CandidateInterventionConfigInput:
    return CandidateInterventionConfigInput(
        interventionType=CandidateInterventionClass.DISTRIBUTION_TAP_OPTIMIZATION,
        yearRange=YEAR_RANGE,
        allocationLimitPerYear=999,
        candidateGeneration=CandidateGenerationConfigInput(
            type=CandidateGenerationType.TAP_OPTIMIZATION,
            averageVoltageSpreadThreshold=40,
            voltageUnderLimitHoursThreshold=48,
            voltageOverLimitHoursThreshold=48,
            tapWeightingFactorLowerThreshold=-10.0,
            tapWeightingFactorUpperThreshold=10.0,
        ),
        # This type allocates directly from candidateGeneration - no candidateAllocationCriteria.
    )


def build_distribution_tx_oltc_candidate() -> CandidateInterventionConfigInput:
    return CandidateInterventionConfigInput(
        interventionType=CandidateInterventionClass.DISTRIBUTION_TX_OLTC,
        yearRange=YEAR_RANGE,
        allocationLimitPerYear=999,
        candidateGeneration=CandidateGenerationConfigInput(
            type=CandidateGenerationType.CRITERIA,
            interventionCriteriaName="<your-candidate-criteria>",  # intervention_candidate_criteria.name
        ),
        candidateAllocationCriteria="<your-allocation-criteria>",  # distribution_transformer_oltc_allocation_criteria.name
        allocationInstanceSelection=["<your-oltc-instance>"],  # distribution_transformer_oltc_instances.name; only 1 allowed
    )


# --- Independent interventions: any combination, with or without a candidate ---------------------

def build_load_reshaping() -> LoadReshapingConfigInput:
    return LoadReshapingConfigInput(
        loadShapeCriteria="<your-load-reshape-strategy>",  # load_reshape_strategies.criteria_name
    )


def build_dvms() -> DvmsConfigInput:
    return DvmsConfigInput(
        lowerLimit=0.9,
        upperLimit=1.1,
        lowerPercentile=5,
        upperPercentile=95,
        maxIterations=3,
        regulatorConfig=DvmsRegulatorConfigInput(
            puTarget=1.0,
            puDeadbandPercent=3,
            maxTapChangePerStep=2,
            allowPushToLimit=False,
        ),
    )


def build_phase_rebalancing() -> PhaseRebalanceProportionsInput:
    # Normalized internally, so a=b=c=1 is an even distribution.
    return PhaseRebalanceProportionsInput(a=1, b=1, c=1)


# --- Assemble the intervention block ------------------------------------------------------------

CANDIDATE_BUILDERS = {
    CandidateInterventionClass.COMMUNITY_BESS: build_community_bess_candidate,
    CandidateInterventionClass.LV_STATCOMS: build_lv_statcoms_candidate,
    CandidateInterventionClass.DISTRIBUTION_TAP_OPTIMIZATION: build_distribution_tap_optimization_candidate,
    CandidateInterventionClass.DISTRIBUTION_TX_OLTC: build_distribution_tx_oltc_candidate,
}


# Unset blocks are left as None, which disables that intervention.
def build_intervention() -> InterventionConfigInput:
    return InterventionConfigInput(
        parentWorkPackageId=PARENT_WORK_PACKAGE_ID,
        candidateIntervention=CANDIDATE_BUILDERS[CANDIDATE_INTERVENTION]() if CANDIDATE_INTERVENTION else None,
        loadReshaping=build_load_reshaping() if ENABLE_LOAD_RESHAPING else None,
        phaseRebalanceProportions=build_phase_rebalancing() if ENABLE_PHASE_REBALANCING else None,
        dvms=build_dvms() if ENABLE_DVMS else None,
    )


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    # Must match the parent work package's config apart from the intervention block, otherwise
    # result differences can't be attributed to the intervention.
    forecast_config = ForecastConfigInput(
        feeders=config["feeders"],
        years=config["forecast_years"],
        scenarios=config["scenarios"],
        timePeriod=TimePeriodInput(
            startTime=datetime.fromisoformat(config["load_time"]["start1"]),
            endTime=datetime.fromisoformat(config["load_time"]["end1"]),
        )
    )

    intervention_config = build_intervention()

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
                        # Candidate interventions will fail to build unless this is ADDITIVE (the default).
                        feederScenarioAllocationStrategy=HcFeederScenarioAllocationStrategy.ADDITIVE,
                        closedLoopVRegEnabled=False,
                        seed=123,
                        # Candidate interventions need distTransformers zones, not Switch / LV feeder.
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
