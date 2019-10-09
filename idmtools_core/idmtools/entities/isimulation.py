import typing
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field

from idmtools.entities.iroot_item import IRootItem
from idmtools.core.interfaces.iassets_enabled import IAssetsEnabled

if typing.TYPE_CHECKING:
    from idmtools.core.types import TExperiment


@dataclass
class ISimulation(IAssetsEnabled, IRootItem, metaclass=ABCMeta):
    """
    Class that epresents a generic simulation.
    This class needs to be implemented for each model type with specifics.
    """

    @abstractmethod
    def set_parameter(self, name: str, value: any) -> dict:
        """
        Set a parameter in the simulation.

        Args:
            name: The name of the parameter.
            value: The value of the parameter.

        Returns:    
            Tag to record the change.
        """
        pass

    @abstractmethod
    def get_parameter(self, name, default=None):
        """
        Get a parameter in the simulation.

        Args:
            name: The name of the parameter.

        Returns: 
            The value of the parameter.
        """
        return None

    @abstractmethod
    def update_parameters(self, params):
        """
        Bulk update parameter configuration.

        Args:
            params: A dictionary with new values.

        Returns: 
            None
        """
        pass

    def __repr__(self):
        try:
            exp_id = self.experiment.uid
        except IRootItem.NoPlatformException:
            exp_id = 'NoPlatformSet'
        return f"<Simulation: {self.uid} - Exp_id: {exp_id}>"

    def pre_creation(self):
        self.gather_assets()

    def pre_getstate(self):
        """
        Return default values for :meth:`pickle_ignore_fields`. Call before pickling.
        """
        from idmtools.assets import AssetCollection
        from idmtools.core.interfaces.entity_container import EntityContainer
        return {"assets": AssetCollection(), "simulations": EntityContainer()}

    @abstractmethod
    def gather_assets(self):
        """
        Gather all the assets for the simulation.
        """
        pass

    @property
    def experiment(self):
        return self.parent(refresh=False)


TSimulation = typing.TypeVar("TSimulation", bound=ISimulation)
TSimulationClass = typing.Type[TSimulation]
TSimulationBatch = typing.List[TSimulation]
TAllSimulationData = typing.Mapping[TSimulation, typing.Any]
TSimulationList = typing.List[typing.Union[TSimulation, str]]