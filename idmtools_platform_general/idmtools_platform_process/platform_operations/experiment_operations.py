"""
Here we implement the ProcessPlatform experiment operations.

Copyright 2021, Bill & Melinda Gates Foundation. All rights reserved.
"""
import os
import platform
from pathlib import Path
from dataclasses import dataclass
from idmtools.entities.experiment import Experiment
from idmtools_platform_file.platform_operations.experiment_operations import FilePlatformExperimentOperations
from logging import getLogger

user_logger = getLogger('user')


@dataclass
class ProcessPlatformExperimentOperations(FilePlatformExperimentOperations):
    """
    Experiment Operations for Process Platform.
    """

    def platform_run_item(self, experiment: Experiment, dry_run: bool = False, **kwargs):
        """
        Run experiment.
        Args:
            experiment: idmtools Experiment
            dry_run: True/False
            kwargs: keyword arguments used to expand functionality
        Returns:
            None
        """
        # Ensure parent
        experiment.parent.add_experiment(experiment)
        self.platform._metas.dump(experiment.parent)
        # Generate/update metadata
        self.platform._metas.dump(experiment)
        if not dry_run:
            # Commission
            self.platform.submit_job(experiment, **kwargs)

        suite_id = experiment.parent_id or experiment.suite_id
        user_logger.info(f'job_directory: {Path(self.platform.job_directory).resolve()}')
        user_logger.info(f'suite: {str(suite_id)}')
        user_logger.info(f'experiment: {experiment.id}')

    def post_run_item(self, experiment: Experiment, dry_run: bool = False, **kwargs):
        """
        Trigger right after commissioning experiment on platform.

        Args:
            experiment: Experiment just commissioned
            dry_run: True/False
            kwargs: keyword arguments used to expand functionality
        Returns:
            None
        """
        super().post_run_item(experiment)

        if not dry_run:
            if platform.system() in ["Windows"]:
                user_logger.warning(
                    "\n/!\\ WARNING: The current ProcessPlatform only support running Experiment/Simulation on Linux!")
                exit(-1)
            else:
                user_logger.info(
                    f'\nYou may try the following command to check simulations running status: \n  idmtools file {os.path.abspath(self.platform.job_directory)} status --exp-id {experiment.id}')
        else:
            user_logger.warning("\nYou are running with dry_true=True")
