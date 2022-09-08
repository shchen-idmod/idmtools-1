"""
Here we implement the SlurmPlatform operations.

Copyright 2021, Bill & Melinda Gates Foundation. All rights reserved.
"""
import os
import shlex
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from uuid import UUID, uuid4
from logging import getLogger
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Union, Type, Any, Dict
from idmtools.core import EntityStatus, ItemType
from idmtools.core.interfaces.ientity import IEntity
from idmtools.entities import Suite
from idmtools.entities.experiment import Experiment
from idmtools.entities.simulation import Simulation
from idmtools_platform_slurm.assets import generate_script, generate_simulation_script

logger = getLogger(__name__)

SLURM_STATES = dict(
    BOOT_FAIL=EntityStatus.FAILED,
    CANCELLED=EntityStatus.FAILED,
    COMPLETED=EntityStatus.SUCCEEDED,
    DEADLINE=EntityStatus.FAILED,
    FAILED=EntityStatus.FAILED,
    OUT_OF_MEMORY=EntityStatus.FAILED,
    PENDING=EntityStatus.RUNNING,
    PREEMPTED=EntityStatus.FAILED,
    RUNNING=EntityStatus.RUNNING,
    REQUEUED=EntityStatus.RUNNING,
    RESIZING=EntityStatus.RUNNING,
    REVOKED=EntityStatus.FAILED,
    SUSPENDED=EntityStatus.FAILED,
    TIMEOUT=EntityStatus.FAILED
)

SLURM_MAPS = {
    "0": EntityStatus.SUCCEEDED,
    "-1": EntityStatus.FAILED,
    "100": EntityStatus.RUNNING,
    "None": EntityStatus.CREATED
}

DEFAULT_SIMULATION_BATCH = """#!/bin/bash
"""


class SlurmOperationalMode(Enum):
    SSH = 'ssh'
    LOCAL = 'local'


@dataclass
class SlurmOperations(ABC):
    platform: 'SlurmPlatform'  # noqa: F821
    platform_type: Type = field(default=None)

    @abstractmethod
    def get_directory(self, item: IEntity) -> Path:
        pass

    @abstractmethod
    def get_directory_by_id(self, item_id: str, item_type: ItemType) -> Path:
        pass

    @abstractmethod
    def make_command_executable(self, simulation: Simulation) -> None:
        pass

    @abstractmethod
    def mk_directory(self, item: IEntity) -> None:
        pass

    @abstractmethod
    def link_file(self, target: Union[Path, str], link: Union[Path, str]) -> None:
        pass

    @abstractmethod
    def link_dir(self, target: Union[Path, str], link: Union[Path, str]) -> None:
        pass

    @abstractmethod
    def update_script_mode(self, script_path: Union[Path, str], mode: int) -> None:
        pass

    @abstractmethod
    def make_command_executable(self, simulation: Simulation) -> None:
        pass

    @abstractmethod
    def create_batch_file(self, item: IEntity, **kwargs) -> None:
        pass

    @abstractmethod
    def submit_job(self, item: Union[Experiment, Simulation], **kwargs) -> Any:
        pass

    @abstractmethod
    def get_simulation_status(self, sim_id: Union[UUID, str]) -> Any:
        pass


@dataclass
class RemoteSlurmOperations(SlurmOperations):
    hostname: str = field(default=None)
    username: str = field(default=None)
    key_file: str = field(default=None)
    port: int = field(default=22)

    def get_directory(self, item: IEntity) -> Path:
        pass

    def get_directory_by_id(self, item_id: str, item_type: ItemType) -> Path:
        pass

    def mk_directory(self, item: IEntity) -> None:
        pass

    def link_file(self, target: Union[Path, str], link: Union[Path, str]) -> None:
        pass

    def link_dir(self, target: Union[Path, str], link: Union[Path, str]) -> None:
        pass

    def update_script_mode(self, script_path: Union[Path, str], mode: int) -> None:
        pass

    def make_command_executable(self, simulation: Simulation) -> None:
        pass

    def create_batch_file(self, item: IEntity, **kwargs) -> None:
        pass

    def submit_job(self, item: Union[Experiment, Simulation], **kwargs) -> Any:
        pass

    def get_simulation_status(self, sim_id: Union[UUID, str]) -> Any:
        pass


@dataclass
class LocalSlurmOperations(SlurmOperations):

    def get_directory(self, item: Union[Suite, Experiment, Simulation]) -> Path:
        """
        Get item's path.
        Args:
            item: Suite, Experiment, Simulation
        Returns:
            item file directory
        """
        if isinstance(item, Suite):
            item_dir = Path(self.platform.job_directory, item.id)
        elif isinstance(item, Experiment):
            suite_id = item.parent_id or item.suite_id
            if suite_id is None:
                raise RuntimeError("Experiment missing parent!")
            suite_dir = Path(self.platform.job_directory, str(suite_id))
            item_dir = Path(suite_dir, item.id)
        elif isinstance(item, Simulation):
            exp = item.parent
            if exp is None:
                raise RuntimeError("Simulation missing parent!")
            exp_dir = self.get_directory(exp)
            item_dir = Path(exp_dir, item.id)
        else:
            raise RuntimeError(f"Get directory is not supported for {type(item)} object on SlurmPlatform")

        return item_dir

    def get_directory_by_id(self, item_id: str, item_type: ItemType) -> Path:
        """
        Get item's path.
        Args:
            item_id: entity id (Suite, Experiment, Simulation)
            item_type: the type of items (Suite, Experiment, Simulation)
        Returns:
            item file directory
        """
        if item_type is ItemType.SIMULATION:
            pattern = f"*/*/{item_id}"
        elif item_type is ItemType.EXPERIMENT:
            pattern = f"*/{item_id}"
        elif item_type is ItemType.SUITE:
            pattern = f"{item_id}"
        else:
            raise RuntimeError(f"Unknown item type: {item_type}")

        root = Path(self.platform.job_directory)
        for item_path in root.glob(pattern=pattern):
            return item_path
        raise RuntimeError(f"Not found path for item_id: {item_id} with type: {item_type}.")

    def mk_directory(self, item: Union[Suite, Experiment, Simulation] = None, dest: Union[Path, str] = None,
                     exist_ok: bool = True) -> None:
        """
        Make a new directory.
        Args:
            item: Suite/Experiment/Simulation
            dest: the folder path
            exist_ok: True/False
        Returns:
            None
        """
        if dest is not None:
            target = Path(dest)
        elif isinstance(item, (Suite, Experiment, Simulation)):
            target = self.get_directory(item)
        else:
            raise RuntimeError('Only support Suite/Experiment/Simulation or not None dest.')
        target.mkdir(parents=True, exist_ok=exist_ok)

    def link_file(self, target: Union[Path, str], link: Union[Path, str]) -> None:
        """
        Link files.
        Args:
            target: the source file path
            link: the file path
        Returns:
            None
        """
        target = Path(target).absolute()
        link = Path(link).absolute()
        link.symlink_to(target)

    def link_dir(self, target: Union[Path, str], link: Union[Path, str]) -> None:
        """
        Link directory/files.
        Args:
            target: the source folder path.
            link: the folder path
        Returns:
            None
        """
        target = Path(target).absolute()
        link = Path(link).absolute()
        link.symlink_to(target)

    @staticmethod
    def update_script_mode(script_path: Union[Path, str], mode: int = 0o777) -> None:
        """
        Change file mode.
        Args:
            script_path: script path
            mode: permission mode
        Returns:
            None
        """
        script_path = Path(script_path)
        script_path.chmod(mode)

    def make_command_executable(self, simulation: Simulation) -> None:
        """
        Make simulation command executable
        Args:
            simulation: idmtools Simulation
        Returns:
            None
        """
        exe = simulation.task.command.executable
        if exe == 'singularity':
            # split the command
            cmd = shlex.split(simulation.task.command.cmd.replace("\\", "/"))
            # get real executable
            exe = cmd[3]

        sim_dir = self.get_directory(simulation)
        exe_path = sim_dir.joinpath(exe)

        # see if it is a file
        if exe_path.exists():
            exe = exe_path
        elif shutil.which(exe) is not None:
            exe = Path(shutil.which(exe))
        else:
            logger.debug(f"Failed to find executable: {exe}")
            exe = None
        try:
            if exe and not os.access(exe, os.X_OK):
                self.update_script_mode(exe)
        except:
            logger.debug(f"Failed to change file mode for executable: {exe}")

    def create_batch_file(self, item: Union[Experiment, Simulation], **kwargs) -> None:
        """
        Create batch file.
        Args:
            item: the item to build batch file for
            kwargs: keyword arguments used to expand functionality.
        Returns:
            None
        """
        if isinstance(item, Experiment):
            max_running_jobs = kwargs.get('max_running_jobs', None)
            generate_script(self.platform, item, max_running_jobs)
        elif isinstance(item, Simulation):
            retries = kwargs.get('retries', None)
            generate_simulation_script(self.platform, item, retries)
        else:
            raise NotImplementedError(f"{item.__class__.__name__} is not supported for batch creation.")

    def submit_job(self, item: Union[Experiment, Simulation], **kwargs) -> Any:
        """
        Submit a Slurm job.
        Args:
            item: idmtools Experiment or Simulation
            kwargs: keyword arguments used to expand functionality
        Returns:
            Any
        """
        if isinstance(item, Experiment):
            working_directory = self.get_directory(item)
            result = subprocess.run(['sbatch', '--parsable', 'sbatch.sh'], stdout=subprocess.PIPE,
                                    cwd=str(working_directory))
            slurm_job_id = result.stdout.decode('utf-8').strip().split(';')[0]
            return slurm_job_id
        elif isinstance(item, Simulation):
            pass
        else:
            raise NotImplementedError(f"Submit job is not implemented on SlurmPlatform.")

    def get_simulation_status(self, sim_id: Union[UUID, str], **kwargs) -> EntityStatus:
        """
        Retrieve simulation status.
        Args:
            sim_id: Simulation ID
            kwargs: keyword arguments used to expand functionality
        Returns:
            EntityStatus
        """
        # Workaround (cancelling job not output -1): check if slurm job finished
        sim_dir = self.get_directory_by_id(sim_id, ItemType.SIMULATION)

        # Check process status
        job_status_path = sim_dir.joinpath('job_status.txt')
        if job_status_path.exists():
            status = open(job_status_path).read().strip()
            if status in ['100', '0', '-1']:
                status = SLURM_MAPS[status]
            else:
                status = SLURM_MAPS['100']  # To be safe
        else:
            status = SLURM_MAPS['None']

        return status
