import asyncio
import sys
from datetime import datetime

from zepben.eas import FeederConfigs, ForecastConfig, FixedTimeLoadOverride
from zepben.eas.client.work_package import WorkPackageConfig, TimePeriod, ResultProcessorConfig, StoredResultsConfig, \
    MetricsResultsConfig, WriterConfig, WriterOutputConfig, EnhancedMetricsConfig, GeneratorConfig, ModelConfig, \
    FeederScenarioAllocationStrategy, SolveConfig, RawResultsConfig, FeederConfig, TimePeriodLoadOverride, FixedTime

from utils import get_client, get_config, print_run, get_config_dir


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)

    # Forecast Config example set up
    # This can be set up through config file or by hard coding in the variables.
    forecast_config = ForecastConfig(
        feeders=config["feeders"],
        years=config["forecast_years"],
        scenarios=config["scenarios"],
        load_time=TimePeriod(
            start_time=datetime.fromisoformat(config["load_time"]["start1"]),
            end_time=datetime.fromisoformat(config["load_time"]["end1"]),
            load_overrides=
            {"nmi1": TimePeriodLoadOverride(
                # Override profile needs to have entries covering a single day or a year.
                load_watts=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0,
                            16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0],
                # Amount of entry between watts and var must match if both watts and vars exists.
                load_var=[2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0,
                          16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0],
                gen_var=None,
                gen_watts=None
            )}

        )
    )

    # Feeder Configs example set up
    # More entries can be added into the configs list base on the config supplied (or hard coded)
    feeder_configs = FeederConfigs(
        configs=[
            FeederConfig(
                feeder=config["feeders"][0],
                years=config["forecast_years"],
                scenarios=config["scenarios"],
                load_time=TimePeriod(
                    start_time=datetime.fromisoformat(config["load_time"]["start2"]),
                    end_time=datetime.fromisoformat(config["load_time"]["end2"]),
                    load_overrides=
                    {"nmi1": TimePeriodLoadOverride(
                        # Override profile needs to have entries covering a single day or a year.
                        load_watts=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0,
                                    16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0],
                        # Amount of entry between watts and var must match if both watts and vars exists.
                        load_var=[2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0,
                                  16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0],
                        gen_var=None,
                        gen_watts=None
                    )}
                )
            ),
            # Fixed time example
            FeederConfig(
                feeder=config["feeders"][1],
                years=config["forecast_years"],
                scenarios=config["scenarios"],
                load_time=FixedTime(
                    time=datetime.fromisoformat(config["load_time"]["start1"]),
                    load_overrides=
                    {"nmi2": FixedTimeLoadOverride(
                        # Fixed time load override supports any number of entries.
                        load_watts=[1.0, 2.0, 3.0],
                        # Same matching entry logic applies here when both watts and var exists.
                        load_var=[2.0, 3.0, 4.0],
                        gen_var=None,
                        gen_watts=None
                    )}
                )
            )
        ]
    )

    result = await eas_client.async_run_hosting_capacity_work_package(
        WorkPackageConfig(
            name=config["work_package_name"],
            syf_config=feeder_configs, # Uncomment this and comment out the below syf_config assignment to use feeder configs.
            # syf_config=forecast_config, # Uncomment this and comment out the above syf_config assignment to use forecast config.
            generator_config=GeneratorConfig(
                model=ModelConfig(
                    vmax_pu=1.2,
                    vmin_pu=0.8,
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
                    feeder_scenario_allocation_strategy=FeederScenarioAllocationStrategy.ADDITIVE,
                    closed_loop_v_reg_enabled=False,
                    closed_loop_v_reg_set_point=0.9925,
                    seed=123,
                ),
                solve=SolveConfig(step_size_minutes=30.0),
                raw_results=RawResultsConfig(True, True, True, True, True)
            ),

            result_processor_config=ResultProcessorConfig(
                writer_config=WriterConfig(

                    output_writer_config=WriterOutputConfig(
                        enhanced_metrics_config=EnhancedMetricsConfig(
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                            True,
                        ))),
                stored_results=StoredResultsConfig(True, True, True, True),
                metrics=MetricsResultsConfig(True)
            ),
            quality_assurance_processing=True
        )
    )

    print_run(result)
    await eas_client.aclose()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
