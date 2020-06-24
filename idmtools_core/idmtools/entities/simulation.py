from dataclasses import dataclass, field, fields
from logging import getLogger, DEBUG
from typing import List, Callable, NoReturn, Union, Mapping, Any, Type, TypeVar, Dict, TYPE_CHECKING
from idmtools.assets import AssetCollection, Asset
from idmtools.core import ItemType, NoTaskFound
from idmtools.core.enums import EntityStatus
from idmtools.core.interfaces.iassets_enabled import IAssetsEnabled
from idmtools.core.interfaces.inamed_entity import INamedEntity
from idmtools.entities.task_proxy import TaskProxy
from idmtools.utils.language import get_qualified_class_name_from_obj
if TYPE_CHECKING:
    from idmtools.entities.itask import ITask
    from idmtools.entities.iplatform import IPlatform
    from idmtools.entities.experiment import Experiment


logger = getLogger(__name__)
user_logger = getLogger('user')


@dataclass
class Simulation(IAssetsEnabled, INamedEntity):
    """
    Class that represents a generic simulation.
    This class needs to be implemented for each model type with specifics.
    """
    #: Task representing the configuration of the command to be executed
    task: 'ITask' = field(default=None)  # noqa: F821
    #: Item Type. Should not be changed from Simulation
    item_type: ItemType = field(default=ItemType.SIMULATION, compare=False)
    #: List of hooks that we can modify to add additional behaviour before creation of simulations
    pre_creation_hooks: List[Callable[[], NoReturn]] = field(default_factory=lambda: [Simulation.gather_additional_files])
    #: Control whether we should replace the task with a proxy after creation
    __replace_task_with_proxy: bool = field(default=True, init=False, compare=False)
    #: Ensure we don't gather assets twice
    __additional_files_gathered: bool = field(default=False)
    #: Additional files to be added to the simulation
    additional_files: AssetCollection = field(default=AssetCollection(), compare=False)

    @property
    def experiment(self) -> 'Experiment':  # noqa: F821
        return self.parent

    @experiment.setter
    def experiment(self, experiment: 'Experiment'):  # noqa: F821
        self.parent = experiment

    def __repr__(self):
        return f"<Simulation: {self.uid} - Exp_id: {self.parent_id}>"

    def __hash__(self):
        return id(self.uid)

    def pre_creation(self):
        if self.task is None:
            msg = 'Task is required for simulations'
            user_logger.error(msg)
            raise NoTaskFound(msg)

        if logger.isEnabledFor(DEBUG):
            logger.debug('Calling task pre creation')
        self.task.pre_creation(self)

        # Call all of our hooks
        for x in self.pre_creation_hooks:
            if logger.isEnabledFor(DEBUG):
                logger.debug(f'Calling simulation pre-create hook named '
                             f'{x.__name__ if hasattr(x, "__name__") else str(x)}')
            x(self)

        if self.__class__ is not Simulation:
            # Add a tag to keep the Simulation class name
            sn = get_qualified_class_name_from_obj(self)
            if logger.isEnabledFor(DEBUG):
                logger.debug(f'Setting Simulation Tag "simulation_type" to "{sn}"')
            self.tags["simulation_type"] = sn

        # Add a tag to for task
        if self.task is not None:
            tn = get_qualified_class_name_from_obj(self.task)
            if logger.isEnabledFor(DEBUG):
                logger.debug(f'Setting Simulation Tag "task_type" to "{tn}"')
            self.tags["task_type"] = tn

    def post_creation(self) -> None:
        if logger.isEnabledFor(DEBUG):
            logger.debug('Calling task post creation')
        if self.task is not None and not isinstance(self.task, TaskProxy):
            self.task.post_creation(self)

        if self.__replace_task_with_proxy or (self.parent and self.parent._Experiment__replace_task_with_proxy):
            if logger.isEnabledFor(DEBUG):
                logger.debug('Replacing task with proxy')
            self.task = TaskProxy.from_task(self.task)

        # provide a default status if none was provided during creation
        if self.status is None:
            self.status = EntityStatus.CREATED

    def pre_getstate(self):
        """
        Return default values for :meth:`pickle_ignore_fields`. Call before pickling.
        """
        from idmtools.assets import AssetCollection
        from idmtools.core.interfaces.entity_container import EntityContainer
        return {"assets": AssetCollection(), "simulations": EntityContainer()}

    def gather_assets(self):
        pass

    def gather_additional_files(self):
        """
        Gather the additional, per-simulation files/transient assets.
        """
        if not self.__additional_files_gathered:
            self.task.gather_transient_assets()
            self.additional_files = self.task.transient_assets
        self.__additional_files_gathered = True

    @classmethod
    def from_task(cls, task: 'ITask', tags: Dict[str, Any] = None,  # noqa E821
                  asset_collection: AssetCollection = None):
        """
        Create a simulation from a task

        Args:
            task: Task to create from
            tags: Tags to create on the simulation
            asset_collection: Simulation Assets

        Returns:

        """
        return Simulation(task=task, tags=dict() if tags is None else tags,
                          assets=asset_collection if asset_collection else AssetCollection())

    def list_static_assets(self, platform: 'IPlatform' = None, **kwargs) -> List[Asset]:
        """
        List assets that have been uploaded to a server already

        Args:
            children: When set to true, simulation assets will be loaded as well
            platform: Optional platform to load assets list from
            **kwargs:

        Returns:
            List of assets
        """
        if self.id is None:
            raise ValueError("You can only list static assets on an existing experiment")
        p = super()._check_for_platform_from_context(platform)
        return p._simulations.list_assets(self, **kwargs)

    def to_dict(self) -> Dict:
        """
        Do a lightweight conversation to json
        Returns:
            Dict representing json of object
        """
        result = dict()
        for f in fields(self):
            if not f.name.startswith("_") and f.name not in ['parent']:
                result[f.name] = getattr(self, f.name)
        result['_uid'] = self.uid
        result['task'] = self.task.to_dict() if self.task else None
        return result


# TODO Rename to T simulation once old simulation is one
TTSimulation = TypeVar("TTSimulation", bound=Simulation)
TTSimulationClass = Type[TTSimulation]
TTSimulationBatch = List[TTSimulation]
TTAllSimulationData = Mapping[TTSimulation, Any]
TTSimulationList = List[Union[TTSimulation, str]]
