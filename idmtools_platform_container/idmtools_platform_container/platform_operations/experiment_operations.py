"""
Here we implement the ProcessPlatform experiment operations.

Copyright 2021, Bill & Melinda Gates Foundation. All rights reserved.
"""
import os
from dataclasses import dataclass
from idmtools.entities.experiment import Experiment
from idmtools_platform_file.platform_operations.experiment_operations import FilePlatformExperimentOperations
from logging import getLogger

logger = getLogger(__name__)
user_logger = getLogger('user')


@dataclass
class ContainerPlatformExperimentOperations(FilePlatformExperimentOperations):
    """
    Experiment Operations for Process Platform.
    """

    def platform_run_item(self, experiment: Experiment, **kwargs):
        """
        Run experiment.
        Args:
            experiment: idmtools Experiment
            kwargs: keyword arguments used to expand functionality
        Returns:
            None
        """
        super().platform_run_item(experiment, **kwargs)
        # Commission
        self.platform.submit_job(experiment, **kwargs)

    def post_run_item(self, experiment: Experiment, **kwargs):
        """
        Trigger right after commissioning experiment on platform.
        Args:
            experiment: Experiment just commissioned
            kwargs: keyword arguments used to expand functionality
        Returns:
            None
        """
        super().post_run_item(experiment, **kwargs)
        user_logger.info(f"\nContainer ID: {self.platform.container_id}")
        user_logger.info(
            f'\nYou may try the following command to check simulations running status: \n  idmtools file {os.path.abspath(self.platform.job_directory)} status --exp-id {experiment.id}')