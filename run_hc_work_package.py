import asyncio
import sys
from datetime import datetime

from zepben.eas.client.work_package import WorkPackageConfig, TimePeriod, ResultProcessorConfig, StoredResultsConfig, \
    MetricsResultsConfig, WriterConfig, WriterOutputConfig, EnhancedMetricsConfig, GeneratorConfig, ModelConfig, \
    FeederScenarioAllocationStrategy, SolveConfig, RawResultsConfig

from utils import get_client, get_config, print_result, get_config_dir


async def main(argv):
    config_dir = get_config_dir(argv)
    config = get_config(config_dir)
    eas_client = get_client(config_dir)
    result = await eas_client.async_run_hosting_capacity_work_package(
        WorkPackageConfig(
            name="test",
            feeders=config["feeders"],
            years=config["forecast_years"],
            scenarios=config["scenarios"],
            load_time=TimePeriod(
                start_time=datetime.fromisoformat(config["load_time"]["start"]),
                end_time=datetime.fromisoformat(config["load_time"]["end"])
            ),
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

    print_result(result)
    await eas_client.aclose()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(sys.argv))
