"""
Here we implement the SlurmPlatform operations interfaces.

Copyright 2021, Bill & Melinda Gates Foundation. All rights reserved.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Type, Union, Any
from uuid import UUID

from idmtools.core import ItemType
from idmtools.core.interfaces.ientity import IEntity
from idmtools.entities.experiment import Experiment
from idmtools.entities.simulation import Simulation


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
    def mk_directory(self, item: IEntity, exist_ok: bool = False) -> None:
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
