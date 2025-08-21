import asyncio
import os

import click
import yaml
from zepben.eas import WorkPackageConfig

from zepben.hosting_capacity_runner import pass_environment
from zepben.hosting_capacity_runner.utils import print_cancel, run_async, print_progress
from zepben.hosting_capacity_runner.work_package_utils import (
    parse_generator_config, parse_forecast_config, parse_results_processor_config, parse_feeder_configs
)


@click.group()
def cli():
    """Operate on Work Packages"""
    pass


@cli.command()
@click.argument("work-package-id", type=str)
@pass_environment
def cancel(ctx, work_package_id):
    """
    Cancel work package
    """

    async def main():
        eas_client = ctx.eas_client
        try:
            result = await eas_client.async_cancel_hosting_capacity_work_package(work_package_id)
            print_cancel(result)
        except Exception as e:
            print(e)

    click.echo(f"Cancelling work package {work_package_id}")

    run_async(main)


@cli.command()
@click.option("--poll", required=False, type=bool, default=False, help=
    "Poll for work package status")
@pass_environment
def progress(ctx, poll):
    """
    Poll for work package status
    """
    eas_client = ctx.eas_client

    async def main():
        while poll:
            try:
                result = await eas_client.async_get_hosting_capacity_work_packages_progress()
                print("Press Ctrl + C to stop monitor...")
                print_progress(result)
            except Exception as e:
                print(e)
            await asyncio.sleep(5)

    run_async(main)


@cli.group()
@pass_environment
def run(ctx):
    """
    Contains commands for running work packages.
    """


@run.command()
@click.option('-n', '--configuration-name', default='feeder_override/example.yaml')
@click.argument('work-package-name', type=str)
@pass_environment
def feeder_override(ctx, configuration_name, work_package_name):
    """
    This script provides an example of how to run a work package with configuration for overriding the load data for specific
    loads in the feeders. This allows you to perform single timestep, fixed time studies for a feeder.
    Note overrides are experimental features, and this entails advanced usage of the HCM module.
    Please contact Zepben to ensure you are creating an efficient and scalable solution with these features.
    """
    click.echo("Feeder override")
    with open(os.path.join(ctx.config_path, 'run_configurations', configuration_name)) as f:
        configuration = yaml.safe_load(f.read())
    configuration['name'] = work_package_name
    configuration = parse_generator_config(
        parse_feeder_configs(
            parse_results_processor_config(
                configuration
            )
        )
    )
    print(configuration)

    async def main():
        eas_client = ctx.eas_client
        try:
            result = await eas_client.async_run_hosting_capacity_work_package(WorkPackageConfig(**configuration))
            click.echo(result)
        except Exception as e:
            click.echo(e)

    run_async(main)


# TODO: I wonder how useful being able to specify different syf_config, generator_config, and result_processor_configs would be?
@run.command()
@click.option('-n', '--configuration-name', default='forecast/example.yaml')
@click.argument('work-package-name', type=str)
@pass_environment
def forecast(ctx, configuration_name, work_package_name):
    """
    This script provides an example of how to run a forecast work package for long term planning studies.
    It allows you to configure a WorkPackage to run 10+ years of timeseries load flows for a given set of scenarios for a
    configurable set of feeders.
    """
    with open(os.path.join(ctx.config_path, 'run_configurations', configuration_name)) as f:
        configuration = yaml.safe_load(f.read())
    configuration['name'] = work_package_name
    configuration = parse_generator_config(
        parse_forecast_config(
            parse_results_processor_config(
                configuration
            )
        )
    )

    async def main():
        eas_client = ctx.eas_client
        try:
            result = await eas_client.async_run_hosting_capacity_work_package(WorkPackageConfig(**configuration))
            click.echo(result)
        except Exception as e:
            click.echo(e)

    run_async(main)


# TODO: should we have a flag here to run the first n feeders pulled straight from EWB?
@run.command()
@click.option('-n', '--configuration-name', default='calibration/example.yaml')
@click.option('--tx-tap-settings', help=
    'The name of a set of previously generated tap settings that are to be applied before running '
    'the calibration work package.')
@pass_environment
def calibration(ctx, configuration_name, tx_tap_settings):
    """
    Perform a calibration run which will utilise PQV data to model the network,
    and output voltage deltas between the PQV actuals and the simulated network.
    Find more information on calibration at:
        https://zepben.github.io/evolve/docs/hosting-capacity-service/docs/next/how-to-guides/calibration#option-2-using-the-python-api

    Use the returned result with `calibration run` to monitor
    """
    with open(os.path.join(ctx.config_path, 'run_configurations', configuration_name)) as f:
        configuration = yaml.safe_load(f.read())
    if tx_tap_settings:
        configuration['transformer_tap_settings'] = tx_tap_settings

    configuration = parse_generator_config(configuration)

    async def main():
        eas_client = ctx.eas_client
        try:
            result = await eas_client.async_run_hosting_capacity_calibration(**configuration)
            click.echo(result)
        except Exception as e:
            click.echo(e)

    run_async(main)
