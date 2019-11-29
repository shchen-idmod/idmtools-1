import ast
from abc import ABCMeta, abstractmethod, ABC
from dataclasses import field, fields, dataclass
from itertools import groupby
from logging import getLogger

from idmtools.core.interfaces.ientity import IEntity, IEntityList
from idmtools.core import CacheEnabled, ItemType, UnknownItemException
from idmtools.entities import IExperiment
from idmtools.entities.iexperiment import IDockerExperiment, IGPUExperiment
from idmtools.services.platforms import PlatformPersistService
from idmtools.core.interfaces.iitem import IItem, IItemList
from typing import Dict, List, NoReturn, Set, Any, Type, TypeVar
from uuid import UUID

from idmtools.utils.entities import validate_user_inputs_against_dataclass

logger = getLogger(__name__)

CALLER_LIST = ['_create_from_block',    # create platform through Platform Factory
               'fetch',                 # create platform through un-pickle
               'get',                   # create platform through platform spec' get method
               '__newobj__',            # create platform through copy.deepcopy
               '_main']                 # create platform through analyzer manager


@dataclass
class IPlatformIOOperations(ABC):
    parent: 'IPlatform'

    @abstractmethod
    def send_assets(self, item: IItem, **kwargs) -> NoReturn:
        """
        Send the assets for a given item to the platform.

        Args:
            item: The item to process. Expected to have an **assets** attribute containing
                the collection.
            **kwargs: Extra parameters used by the platform.
        """
        pass

    @abstractmethod
    def get_files(self, item: IItem, files: List[str]) -> Dict[str, bytearray]:
        """
        Return a dictionary of the specified files for the specified item.

        Args:
            item: The item to fetch files for.
            files: The list of file names to fetch.

        Returns:
            A dictionary container filename->bytearray.
        """
        pass


@dataclass
class IPlaformMetdataOperations(CacheEnabled, ABC):
    parent: 'IPlatform'
    _object_cache_expiration: 'int' = 60

    @abstractmethod
    def refresh_status(self, item) -> NoReturn:
        """
        Populate the platform item and specified item with its status.

        Args:
            item: The item to check status for.
        """
        pass

    def flatten_item(self, item: IEntity) -> IItemList:
        """
        Flatten an item: resolve the children until getting to the leaves.
        For example, for an experiment, will return all the simulations.
        For a suite, will return all the simulations contained in the suites experiments.

        Args:
            item: Which item to flatten

        Returns:List of leaves

        """
        children = self.get_children(item.uid, item.item_type, force=True)
        if children is None:
            items = [item]
        else:
            items = list()
            for child in children:
                items += self.flatten_item(item=child)
        return items

    @abstractmethod
    def get_platform_item(self, item_id: UUID, item_type: ItemType, **kwargs) -> Any:
        """
        Get an item by its ID. The implementing classes must know how to distinguish
        items of different levels (e.g. simulation, experiment, suite).

        Args:
            item_id: The ID of the item to retrieve.
            item_type: The type of object to retrieve.

        Returns:
            The specified item found on the platform or None.
        """
        pass

    @abstractmethod
    def get_children_for_platform_item(self, platform_item: Any, raw: bool, **kwargs) -> List[Any]:
        """
        Return the list of children for the given platform item.
        For example, an experiment passed to this function will return all the contained simulations.
        The results are either platform items or idm-tools entities depending on the `raw` parameter.

        Args:
            platform_item: Parent item
            raw: Return a platform item if True, an idm-tools entity if false
            **kwargs: Additional platform specific parameters

        Returns:
            A list of children, None if no children
        """
        pass

    @abstractmethod
    def get_parent_for_platform_item(self, platform_item: Any, raw: bool, **kwargs) -> Any:
        """
        Return the parent item for a given platform_item.

        Args:
            platform_item: Child item
            raw: Return a platform item if True, an idm-tools entity if false
            **kwargs: Additional platform specific parameters

        Returns:
            Parent or None
        """
        pass

    def get_item(self, item_id: UUID, item_type: ItemType = None,
                 force: bool = False, raw: bool = False, **kwargs) -> Any:
        """
        Retrieve an object from the platform.
        This function is cached; force allows you to force the refresh of the cache.
        If no **object_type** is passed, the function will try all the types (experiment, suite, simulation).

        Args:
            item_id: The ID of the object to retrieve.
            item_type: The type of the object to be retrieved.
            force: If True, force the object fetching from the platform.
            raw: Return either an |IT_s| object or a platform object.

        Returns:
            The object found on the platform or None.
        """
        if not item_type or item_type not in self.parent.supported_types:
            raise Exception("The provided type is invalid or not supported by this platform...")

        # Create the cache key
        cache_key = f"o_{item_id}_" + ('r' if raw else 'o') + '_'.join(f"{k}_{v}" for k, v in kwargs.items())

        # If force -> delete in the cache
        if force:
            self.cache.delete(cache_key)

        # If we cannot find the object in the cache -> retrieve depending on the type
        if cache_key not in self.cache:
            ce = self.get_platform_item(item_id, item_type, **kwargs)

            # Nothing was found on the platform
            if not ce:
                raise UnknownItemException(f"Object {item_type} {item_id} not found on the platform...")

            # Create the object if we do not want it raw
            if raw:
                return_object = ce
            else:
                return_object = self._platform_item_to_entity(ce, **kwargs)
                return_object.platform = self.parent

            # Persist
            self.cache.set(cache_key, return_object, expire=self._object_cache_expiration)

        else:
            return_object = self.cache.get(cache_key)

        return return_object

    def get_children(self, item_id: UUID, item_type: ItemType,
                     force: bool = False, raw: bool = False, **kwargs) -> Any:
        """
        Retrieve the children of a given object.

        Args:
            item_id: The ID of the object for which we want the children.
            force: If True, force the object fetching from the platform.
            raw: Return either an |IT_s| object or a platform object.
            item_type: Pass the type of the object for quicker retrieval.

        Returns:
            The children of the object or None.
        """
        if not item_type or item_type not in self.parent.supported_types:
            raise Exception("The provided type is invalid or not supported by this platform...")

        # Create the cache key based on everything we pass to the function
        cache_key = f"c_{item_id}" + ('r' if raw else 'o') + '_'.join(f"{k}_{v}" for k, v in kwargs.items())

        if force:
            self.cache.delete(cache_key)

        if cache_key not in self.cache:
            ce = self.get_item(item_id, raw=True, item_type=item_type)
            children = self.get_children_for_platform_item(ce, raw=raw, **kwargs)
            self.cache.set(cache_key, children, expire=self._object_cache_expiration)
            return children

        return self.cache.get(cache_key)

    def get_parent(self, item_id: UUID, item_type: ItemType = None, force: bool = False,
                   raw: bool = False, **kwargs):
        """
        Retrieve the parent of a given object.

        Args:
            item_id: The ID of the object for which we want the parent.
            force: If True, force the object fetching from the platform.
            raw: Return either an |IT_s| object or a platform object.
            item_type: Pass the type of the object for quicker retrieval.

        Returns:
            The parent of the object or None.

        """
        if not item_type or item_type not in self.parent.supported_types:
            raise Exception("The provided type is invalid or not supported by this platform...")

        # Create the cache key based on everything we pass to the function
        cache_key = f'p_{item_id}' + ('r' if raw else 'o') + '_'.join(f"{k}_{v}" for k, v in kwargs.items())

        if force:
            self.cache.delete(cache_key)

        if cache_key not in self.cache:
            ce = self.get_item(item_id, raw=True, item_type=item_type)
            parent = self.get_parent_for_platform_item(ce, raw=raw, **kwargs)
            self.cache.set(cache_key, parent, expire=self._object_cache_expiration)
            return parent

        return self.cache.get(cache_key)

    def _platform_item_to_entity(self, platform_item: Any, **kwargs) -> IEntity:
        """
        Transform a platform object into a idm-tools entity.
        By default pass-through if the platform uses idm-tools entities already (Local and Test).

        Args:
            platform_item: The platform item to transform
            **kwargs: Additional keyword parameters

        Returns:An idm-tools entity
        """
        return platform_item

@dataclass
class IPlatformCommissioningOperations(ABC):
    parent: 'IPlatform'

    @abstractmethod
    def run_items(self, items: IItemList) -> NoReturn:
        """
        Run the items (sims, exps, suites) on the platform
        Args:
            items: The items to run
        """
        pass

    def create_items(self, items: IEntity) -> List[UUID]:
        """
        Create items (simulations, experiments, or suites) on the platform. The function will batch the items based on
        type and call the self._create_batch for creation

        Args:
            items: The list of items to create.

        Returns:
            List of item IDs created.
        """
        for item in items:
            if item.item_type not in self.parent.supported_types:
                raise Exception(f'Unable to create items of type: {item.item_type} for platform: {self.__class__.__name__}')

        ids = []
        for key, group in groupby(items, lambda x: x.item_type):
            ids.extend(self._create_batch(list(group), key))
        return ids

    @abstractmethod
    def _create_batch(self, batch: IEntityList, item_type: ItemType) -> List[UUID]:
        pass


class IPlatform(IItem, CacheEnabled, metaclass=ABCMeta):
    """
    Interface defining a platform.
    A platform needs to implement basic operation such as:

    - Creating experiment
    - Creating simulation
    - Commissioning
    - File handling
    """
    supported_types: 'Set[ItemType]' = field(default_factory=lambda: set(), metadata={"pickle_ignore": True})
    _object_cache_expiration: 'int' = 60
    io: IPlatformIOOperations = None
    commissioning: IPlatformCommissioningOperations = None
    metadata: IPlaformMetdataOperations = None

    @staticmethod
    def get_caller():
        """
        Trace the stack and find the caller.

        Returns:
            The direct caller.
        """
        import inspect

        s = inspect.stack()
        return s[2][3]

    def __new__(cls, *args, **kwargs):
        """
        Create a new object.

        Args:
            args: User inputs.
            kwargs: User inputs.

        Returns:
            The object created.
        """

        # Check the caller
        caller = cls.get_caller()

        # Action based on the caller
        if caller in CALLER_LIST:
            return super().__new__(cls)
        else:
            raise ValueError(
                f"Please use Factory to create Platform! For example: \n    platform = Platform('COMPS', **kwargs)")

    def __post_init__(self) -> NoReturn:
        """
        Work to be done after object creation.

        Returns:
            None
        """
        self.validate_inputs_types()

        # Initialize the cache
        self.initialize_cache()

        # Save itself
        PlatformPersistService.save(self)

    def validate_inputs_types(self) -> NoReturn:
        """
        Validate user inputs and case attributes with the correct data types.

        Returns:
            None
        """
        # retrieve field values, default values and types
        fds = fields(self)
        field_value = {f.name: getattr(self, f.name) for f in fds}
        field_type = {f.name: f.type for f in fds}

        # Make sure the user values have the requested type
        fs_kwargs = validate_user_inputs_against_dataclass(field_type, field_value)

        # Update attr with validated data types
        for fn in fs_kwargs:
            setattr(self, fn, field_value[fn])

    @abstractmethod
    def supported_experiment_types(self) -> List[Type]:
        """
        Returns a list of supported experiment types. These types should be either abstract or full classes that have
            been derived from IExperiment
        Returns:

        """
        return [IExperiment]

    @abstractmethod
    def unsupported_experiment_types(self) -> List[Type]:
        """
        Returns a list of experiment types not supported by the platform. These types should be either abstract or full
            classes that have been derived from IExperiment
        Returns:

        """
        return [IDockerExperiment, IGPUExperiment]

    def is_supported_experiment(self, experiment: IExperiment) -> bool:
        """
        Determines if an experiment is supported by the specified platform.
        Args:
            experiment: Experiment to check

        Returns:
            True is experiment is supported, otherwise, false
        """
        ex_types = set(self.supported_experiment_types())
        if any([isinstance(experiment, t) for t in ex_types]):
            unsupported_types = self.unsupported_experiment_types()
            return not any([isinstance(experiment, t) for t in unsupported_types])
        return False

    def __repr__(self):
        return f"<Platform {self.__class__.__name__} - id: {self.uid}>"


TPlatform = TypeVar("TPlatform", bound=IPlatform)
TPlatformClass = Type[TPlatform]
