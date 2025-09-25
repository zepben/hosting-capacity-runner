from zepben.eas import InterventionConfig, YearRange, InterventionClass, CandidateGenerationConfig, DvmsConfig, \
    RegulatorConfig
from zepben.eas.client.work_package import PhaseRebalanceProportions, CandidateGenerationType

# General notes:
#  - There is a strong argument to move year_range to candidate_generation, since it's only relevant if PRRP is used.
#    This may be done soon if we have the time for it.

# TARIFF_REFORM: Modifies shapes of customer loads.
#                Each load reshape criteria (in the input DB) corresponds to a sequence of load reshape strategies.
#                Each load reshape strategy has:
#                 - A set of criteria for the customers to apply the strategy to e.g. has_ev (boolean), year (int)
#                 - A percentage used to select a portion of the applicable customers
#                 - A load reshape instance, which is basically an additive or multiplicative profile to apply
#                   - Load reshape instances can have profiles a single number long to denote flat application
#                     e.g. [0.5] multiplicative means halve the load, and 48 numbers mean a profile that repeats daily.
# Tables used:
#  - load_reshape_strategies
#  - load_reshape_instances
InterventionConfig(
    # base_work_package_id is only needed for record-keeping in EAS (work package B is intervention on work package A)
    base_work_package_id="550e8400-e29b-41d4-a716-446655440000",
    year_range=YearRange(2026, 2030),  # no effect, but should be set to range of years base WP solved for
    allocation_limit_per_year=0,  # allocation_limit_per_year has no effect. Should probably default to 0
    intervention_type=InterventionClass.TARIFF_REFORM,
    candidate_generation=None,  # PRRP not needed for tariff reform
    allocation_criteria="load_reshape_strategy_1"  # corresponds to load_reshape_strategies.criteria_name in input DB
    # specific_allocation_instance has no effect
    # phase_rebalance_proportions has no effect
    # dvms has no effect
)

# CONTROLLED_LOAD_HOT_WATER: Exactly the same as tariff reform, just under a different name. The umbrella term used
#                            internally to describe both is "load reshaping".
# Tables used:
#  - load_reshape_strategies
#  - load_reshape_instances
InterventionConfig(
    # base_work_package_id is only needed for record-keeping in EAS (work package B is intervention on work package A)
    base_work_package_id="550e8400-e29b-41d4-a716-446655440001",
    year_range=YearRange(2026, 2030),  # no effect, but should be set to range of years base WP solved for
    allocation_limit_per_year=0,  # allocation_limit_per_year has no effect. Should probably default to 0
    intervention_type=InterventionClass.CONTROLLED_LOAD_HOT_WATER,
    candidate_generation=None,  # PRRP not needed for CLHW
    allocation_criteria="load_reshape_strategy_2"  # corresponds to load_reshape_strategies.criteria_name in input DB
    # specific_allocation_instance has no effect
    # phase_rebalance_proportions has no effect
    # dvms has no effect
)

# COMMUNITY_BESS: Adds batteries on LV networks to offset high load/generation. Candidates are ranked by
#                 the sum of gen_exceeding_normal_voltage_cecv + load_exceeding_normal_thermal_voltage_vcr across
#                 the years they each apply.
# Tables used:
#  - intervention_candidate_criteria
#  - bess_instances
#  - intervention_candidates
#  - bess_allocation_criteria
InterventionConfig(
    # base_work_package_id is used by PRRP to query enhanced metrics in the input database
    base_work_package_id="550e8400-e29b-41d4-a716-446655440002",
    year_range=YearRange(
        min_year=2026,  # The earliest year to find and apply intervention candidates for
        max_year=2030  # The latest year to find and apply intervention candidates for
    ),
    allocation_limit_per_year=100,  # maximum number of batteries to install per year
    intervention_type=InterventionClass.COMMUNITY_BESS,
    candidate_generation=CandidateGenerationConfig(
        type=CandidateGenerationType.CRITERIA,  # expected for COMMUNITY_BESS

        # corresponds to intervention_candidate_criteria.name in input DB. Each entry has a suite of optional thresholds
        # e.g. min_voltage_outsite_limits_hours. If all thresholds are exceeded for a year at a measurement zone, it is
        # marked as a candidate for the earliest year that measurement zone breaks the threshold.
        intervention_criteria_name="threshold_set_1"
    ),
    allocation_criteria="bess_allocation_criteria_1",  # corresponds to bess_allocation_criteria.name in input DB.
    specific_allocation_instance="bess_instance_1",  # Optional, corresponds to bess_instances.name in input DB.
                                                     # If this is set, this is the only instance (type) of battery
                                                     # to apply to the model. Otherwise, the smallest viable battery
                                                     # will be allocated in each case.
    # phase_rebalance_proportions has no effect
    # dvms has no effect
)

# DISTRIBUTION_TX_OLTC: Installs on-load tap changers at distribution transformers. In OpenDSS, This is modelled as
#                       adding TapChangerControls to existing distribution transformers with ratio tap changers.
# Tables used:
#  - intervention_candidate_criteria
#  - distribution_transformer_oltc_instances
#  - intervention_candidates
#  - distribution_transformer_oltc_allocation_criteria
InterventionConfig(
    # base_work_package_id is used by PRRP to query enhanced metrics in the input database
    base_work_package_id="550e8400-e29b-41d4-a716-446655440003",
    year_range=YearRange(
        min_year=2026,  # The earliest year to find and apply intervention candidates for
        max_year=2030  # The latest year to find and apply intervention candidates for
    ),
    allocation_limit_per_year=50,  # maximum number of on-load tap changers to install per year
    intervention_type=InterventionClass.DISTRIBUTION_TX_OLTC,
    candidate_generation=CandidateGenerationConfig(
        type=CandidateGenerationType.CRITERIA,  # expected for DISTRIBUTION_TX_OLTC

        # corresponds to intervention_candidate_criteria.name in input DB. Each entry has a suite of optional thresholds
        # e.g. min_voltage_outsite_limits_hours. If all thresholds are exceeded for a year at a measurement zone, it is
        # marked as a candidate for the earliest year that measurement zone breaks the threshold.
        intervention_criteria_name="threshold_set_2"
    ),
    # corresponds to distribution_transformer_oltc_allocation_criteria.name in input DB.
    allocation_criteria="distribution_transformer_oltc_allocation_criteria_1",
    # Optional, corresponds to distribution_transformer_oltc_instances.name in input DB. If this is set, this is the
    # only instance (type) of OLTC to apply to the model. Otherwise, an arbitrary OLTC will be allocated in each case.
    specific_allocation_instance="distribution_transformer_oltc_instance_1",
    # phase_rebalance_proportions has no effect
    # dvms has no effect
)

# LV_STATCOMS: Adds STATCOMs on the LV networks to compensate for reactive excess. In OpenDSS, this is modelled as
#              multiple PVSystems that are controlled by a single InvControl whose characteristics (e.g. I-V curve)
#              determined by the LV STATCOM instance found in the input DB.
# Tables used:
#  - intervention_candidate_criteria
#  - lv_statcom_instances
#  - intervention_candidates
#  - lv_statcom_allocation_criteria
InterventionConfig(
    # base_work_package_id is used by PRRP to query enhanced metrics in the input database
    base_work_package_id="550e8400-e29b-41d4-a716-446655440004",
    year_range=YearRange(
        min_year=2026,  # The earliest year to find and apply intervention candidates for
        max_year=2030  # The latest year to find and apply intervention candidates for
    ),
    allocation_limit_per_year=100,  # maximum number of batteries to install per year
    intervention_type=InterventionClass.LV_STATCOMS,
    candidate_generation=CandidateGenerationConfig(
        type=CandidateGenerationType.CRITERIA,  # expected for LV_STATCOMS

        # corresponds to intervention_candidate_criteria.name in input DB. Each entry has a suite of optional thresholds
        # e.g. min_voltage_outsite_limits_hours. If all thresholds are exceeded for a year at a measurement zone, it is
        # marked as a candidate for the earliest year that measurement zone breaks the threshold.
        intervention_criteria_name="threshold_set_3"
    ),
    # corresponds to lv_statcom_allocation_criteria.name in input DB.
    allocation_criteria="lv_statcom_allocation_criteria_1",
    # Optional, corresponds to lv_statcom_instances.name in input DB. If this is set, this is the only instance (type)
    # of LV STATCOM to apply to the model. Otherwise, an arbitrary LV STATCOM will be allocated in each case.
    specific_allocation_instance="lv_statcom_instance_1",
    # phase_rebalance_proportions has no effect
    # dvms has no effect
)

# DVMS: Done while solving OpenDSS model. Distribution transformers' taps will adjust based on the voltages at the
#       downstream customers (multiple reading points per TX). This is done at each time step when solving--DVMS
#       requires the solver to execute in a special mode where the model is solved 1 time step at a time in order to
#       get the voltages needed to adjust each tap. This is the most involved of all the interventions.
# Tables used: none
InterventionConfig(
    # base_work_package_id is only needed for record-keeping in EAS (work package B is intervention on work package A)
    base_work_package_id="550e8400-e29b-41d4-a716-446655440005",
    year_range=YearRange(2026, 2030),  # no effect, but should be set to range of years base WP solved for
    allocation_limit_per_year=0,  # allocation_limit_per_year has no effect. Should probably default to 0
    intervention_type=InterventionClass.DVMS,
    candidate_generation=None,  # PRRP not needed for DVMS
    # allocation_criteria has no effect
    # specific_allocation_instance has no effect
    # phase_rebalance_proportions has no effect
    dvms=DvmsConfig(
        # The DVMS logic aims to adjust taps such that customers within the given percentile range have p.u. voltages
        # within the [lower_limit, upper_limit] range. In this example config, the customers from the 5th to the 95th
        # percentile in voltages should have voltages within 0.9-1.1 p.u.
        lower_limit=0.9,
        upper_limit=1.1,
        lower_percentile=5,
        upper_percentile=95,

        # The maximum attempts to adjust taps per time step to meet the above requirements
        max_iterations=3,

        # Configures simulated voltage regulator that is responsible for fulfilling the above requirements.
        # Note that the above requirements control acceptance (whether to move on to the next time step), whereas
        # these parameters configure the actual logic used to determine tap position changes.
        regulator_config=RegulatorConfig(
            pu_target=1.0,
            # interpreted as the whole width of the deadband in % of the target, so the deadband is 0.94-1.06 p.u. here.
            pu_deadband_percent=12,
            max_tap_change_per_step=2,
            # if True, tap changes will be made if they sufficiently improve one side of the customer voltage
            # distribution, even if they worsen the other. For example, suppose a +2 tap change is sufficient to reduce
            # the percentage of customers below 0.9 p.u. voltage to under 5 percent. Even if the percentage of customers
            # that are above 1.1 p.u. voltage increases to 20 percent, the tap change will be attempted (acceptance
            # criteria is still checked for the number of iterations specified above).
            allow_push_to_limit=True
        )
    )
)

# PHASE_REBALANCING: Redistributes single-phase customers across A/B/C phases in the specified proportions.
#                    This should be applied on networks we know to already have an uneven distribution of single-phase
#                    customers across the three phases, which should be modelled in the base network in EWB.
# Tables used: none
InterventionConfig(
    # base_work_package_id is only needed for record-keeping in EAS (work package B is intervention on work package A)
    base_work_package_id="550e8400-e29b-41d4-a716-446655440006",
    year_range=YearRange(2026, 2030),  # no effect, but should be set to range of years base WP solved for
    allocation_limit_per_year=0,  # allocation_limit_per_year has no effect. Should probably default to 0
    intervention_type=InterventionClass.PHASE_REBALANCING,
    candidate_generation=None,  # PRRP not needed for phase rebalancing
    # allocation_criteria has no effect
    # specific_allocation_instance has no effect
    phase_rebalance_proportions=PhaseRebalanceProportions(
        # proportions used to reallocate single-phase customers. This does not have to sum to 1, but the sum should be
        # positive and none of the values should be negative. For an even distribution, use values 1, 1, 1.
        a=0.25,
        b=0.35,
        c=0.4
    )
    # dvms has no effect
)

# DISTRIBUTION_TAP_OPTIMIZATION: Identifies zones in the network with exceptionally high/low voltage over each year
#                                and uses a heuristic system to work out a possibly beneficial tap setting change
#                                for each case. Note that taps settings are changed at most yearly in this system rather
#                                than possibly each time step, as is the case in DVMS. This is also not a feedback
#                                system like in DVMS--tap change candidates are generated by PRRP once using the base
#                                work package's results rather than in each time step in solve-time.
# Tables used: none
InterventionConfig(
    # base_work_package_id is used by PRRP to query enhanced metrics in the input database
    base_work_package_id="550e8400-e29b-41d4-a716-446655440007",
    year_range=YearRange(
        min_year=2026,  # The earliest year to find and apply intervention candidates for
        max_year=2030  # The latest year to find and apply intervention candidates for
    ),
    allocation_limit_per_year=10,  # maximum number of tap settings to change per year
    intervention_type=InterventionClass.DISTRIBUTION_TAP_OPTIMIZATION,
    candidate_generation=CandidateGenerationConfig(
        type=CandidateGenerationType.TAP_OPTIMIZATION,  # expected for DISTRIBUTION_TAP_OPTIMIZATION

        # The following thresholds apply to each measurement zone for each year
        voltage_delta_avg_threshold=0.05,  # threshold for average deviation in voltage p.u. across the transformer
        voltage_under_limit_hours_threshold=48,  # threshold for hours a transformer is below nominal voltage range
        voltage_over_limit_hours_threshold=48,  # threshold for hours a transformer is below nominal voltage range
        # Tap weighting factor is used when there are competing thresholds are exceeded in the same year for the same
        # measurement zone. It considers how severe voltage deviation is for the 1st and 99th percentile of time and
        # the number of hours spent outside the nominal voltage range in either direction. The below values are sensible
        # for most cases.
        tap_weighting_factor_lower_threshold=-10.0,
        tap_weighting_factor_upper_threshold=10.0
    ),
    # allocation_criteria has no effect
    # specific_allocation_instance has no effect
    # phase_rebalance_proportions has no effect
    # dvms has no effect
)
