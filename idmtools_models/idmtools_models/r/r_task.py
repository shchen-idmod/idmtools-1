import os
from dataclasses import field, dataclass
from logging import getLogger
from typing import Type
from idmtools.assets import Asset, AssetCollection
from idmtools.core.docker_task import DockerTask
from idmtools.entities import CommandLine
from idmtools.entities.simulation import Simulation
from idmtools.registry.task_specification import TaskSpecification

logger = getLogger(__name__)


@dataclass
class RTask(DockerTask):
    script_path: str = field(default=None)
    r_path: str = field(default='Rscript')
    extra_libraries: list = field(default_factory=lambda: [], compare=False, metadata={"md": True})

    def __post_init__(self):
        super().__post_init__()
        if self.script_path is None:
            raise ValueError("Script name is required")
        cmd_str = f'{self.r_path} ./Assets/{os.path.basename(self.script_path)}'
        self._task_log.info('Setting command line to %s', cmd_str)
        self.command = CommandLine(cmd_str)

    def reload_from_simulation(self, simulation: Simulation, **kwargs):
        logger.debug("Reload from simulation")
        # check experiment level assets for items
        if simulation.parent.assets:
            new_assets = AssetCollection()
            for i, asset in enumerate(simulation.parent.assets.assets):
                if asset.filename != self.script_path and asset.absolute_path != self.script_path:
                    new_assets.add_asset(asset)
            simulation.parent.assets = new_assets

    def gather_common_assets(self) -> AssetCollection:
        """
        Gather R Assets
        Returns:

        """
        super().gather_common_assets()
        self._task_log.info('Adding Common asset from %s', self.script_path)
        self.common_assets.add_or_replace_asset(Asset(absolute_path=self.script_path))
        return self.common_assets

    def gather_transient_assets(self) -> AssetCollection:
        """
        Gather transient assets. Generally this is the simulation level assets

        Returns:

        """
        return self.transient_assets


class RTaskSpecification(TaskSpecification):

    def get(self, configuration: dict) -> RTask:
        """
        Get instance of RTask

        Args:
            configuration: configuration for task

        Returns:
            RTask with configuration
        """
        return RTask(**configuration)

    def get_description(self) -> str:
        """
        Returns the Description of the plugin

        Returns:
            Plugin Description
        """
        return "Defines a R script command"

    def get_type(self) -> Type[RTask]:
        """
        Get Type for Plugin

        Returns:
            RTask
        """
        return RTask
