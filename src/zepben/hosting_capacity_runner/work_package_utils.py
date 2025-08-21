from zepben.eas import ModelConfig, GeneratorConfig, TimePeriod, ForecastConfig, SolveConfig, RawResultsConfig, \
    ResultProcessorConfig, WriterConfig, EnhancedMetricsConfig, StoredResultsConfig, MetricsResultsConfig, \
    WriterOutputConfig, FeederConfigs, FeederConfig, FixedTime, FixedTimeLoadOverride


def parse_generator_config(configuration: dict) -> dict:
    if gen_cfg := configuration.get('generator_config'):
        if gen_model_cfg := gen_cfg.get('model'):
            configuration['generator_config']['model'] = ModelConfig(**gen_model_cfg)

        if solve_cfg := gen_cfg.get('solve'):
            configuration['generator_config']['solve'] = SolveConfig(**solve_cfg)

        if raw_results_cfg := gen_cfg.get('raw_results'):
            configuration['generator_config']['raw_results'] = RawResultsConfig(**raw_results_cfg)

        configuration['generator_config'] = GeneratorConfig(**gen_cfg)

    return configuration

def parse_forecast_config(configuration: dict) -> dict:
    if forecast_cfg := configuration.get('syf_config'):
        if load_time := forecast_cfg.get('load_time'):
            configuration['syf_config']['load_time'] = TimePeriod(**load_time)

        configuration['syf_config'] = ForecastConfig(**forecast_cfg)

    return configuration

def parse_feeder_configs(configuration: dict) -> dict:
    if feeder_cfgs := configuration.get('syf_config'):
        if feeder_cfg := feeder_cfgs.get('configs'):
            f_configs = []
            for cfg in feeder_cfg:
                if load_time := cfg.get('load_time'):
                    if load_overrides := load_time.get('load_overrides'):
                        load_time['load_overrides'] = {k: FixedTimeLoadOverride(**v) for k, v in load_overrides.items()}
                    cfg['load_time'] = FixedTime(**load_time)
                f_configs.append(FeederConfig(**cfg))
            feeder_cfgs['configs'] = f_configs
        configuration['syf_config'] = FeederConfigs(**feeder_cfgs)

    return configuration

def parse_results_processor_config(configuration: dict) -> dict:
    if results_processor_cfg := configuration.get('result_processor_config'):
        if writer_cfg := results_processor_cfg.get('writer_config'):
            if output_writer_cfg := writer_cfg.get('output_writer_config'):
                if enhanced_metrics_cfg := output_writer_cfg.get('enhanced_metrics_config'):
                    output_writer_cfg['enhanced_metrics_config'] = EnhancedMetricsConfig(**enhanced_metrics_cfg)

                writer_cfg['output_writer_config'] = WriterOutputConfig(**output_writer_cfg)

            results_processor_cfg['writer_config'] = WriterConfig(**writer_cfg)

        if stored_results_cfg := results_processor_cfg.get('stored_results'):
            results_processor_cfg['stored_results'] = StoredResultsConfig(**stored_results_cfg)

        if metrics_cfg := results_processor_cfg.get('metrics'):
            results_processor_cfg['metrics'] = MetricsResultsConfig(**metrics_cfg)

        configuration['result_processor_config'] = ResultProcessorConfig(**results_processor_cfg)

    return configuration
