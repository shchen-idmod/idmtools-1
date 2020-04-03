import logging
import click
from idmtools import IdmConfigParser
from idmtools.core.logging import setup_logging
from idmtools_cli.iplatform_cli import IPlatformCLI

# Decorator for CLI functions that will require a platform object passed down to them
pass_platform_cli = click.make_pass_decorator(IPlatformCLI)


@click.group()
@click.option('--debug/--no-debug', default=False, help="When selected, enables console level logging")
def cli(debug):
    """
    Allows you to perform multiple idmtools commands

    """
    IdmConfigParser()
    # init config by just calling config parser
    if debug:
        setup_logging(console=True, level=logging.DEBUG)