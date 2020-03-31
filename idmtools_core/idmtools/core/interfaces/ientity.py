from abc import ABCMeta
from dataclasses import dataclass, field
from typing import NoReturn, List, Any, Dict, Union
from uuid import UUID

from idmtools.core import EntityStatus, ItemType, NoPlatformException
from idmtools.core.interfaces.iitem import IItem
from idmtools.services.platforms import PlatformPersistService


@dataclass
class IEntity(IItem, metaclass=ABCMeta):
    """
    Interface for all entities in the system.
    """
    platform_id: UUID = field(default=None, compare=False, metadata={"md": True})
    _platform: 'IPlatform' = field(default=None, compare=False, metadata={"pickle_ignore": True})  # noqa E821
    parent_id: UUID = field(default=None, metadata={"md": True})
    _parent: 'IEntity' = field(default=None, compare=False, metadata={"pickle_ignore": True})
    status: EntityStatus = field(default=None, compare=False, metadata={"pickle_ignore": True})
    tags: Dict[str, Any] = field(default_factory=lambda: {}, metadata={"md": True})
    item_type: ItemType = field(default=None, compare=False)
    # Platform
    _platform_object: Any = field(default=None, compare=False, metadata={"pickle_ignore": True})

    def update_tags(self, tags: dict = None) -> NoReturn:
        """
        Shortcut to update the tags with the given dictionary
        Args:
            tags: New tags
        """
        self.tags.update(tags)

    def post_creation(self) -> None:
        self.status = EntityStatus.CREATED

    @classmethod
    def from_id(cls, item_id: Union[str, UUID], platform: 'IPlatform' = None) -> 'IEntity':  # noqa E821
        if platform is None:
            from idmtools.core.platform_factory import current_platform
            if current_platform is None:
                raise ValueError("You have to specify a platfrom to load the asset collection from")
            platform = current_platform
        if cls.item_type is None:
            raise EnvironmentError("ItemType is None. This is most likely a badly derived IEntity "
                                   "that doesn't run set the default item type on the class")
        return platform.get_item(item_id, cls.item_type)

    @property
    def parent(self):
        if not self._parent:
            if not self.parent_id:
                return None
            if not self.platform:
                raise NoPlatformException("The object has no platform set...")
            self._parent = self.platform.get_parent(self.uid, self.item_type)

        return self._parent

    @parent.setter
    def parent(self, parent):
        if parent:
            self._parent = parent
            self.parent_id = parent.uid
        else:
            self.parent_id = self._parent = None

    @property
    def platform(self) -> 'IPlatform':  # noqa E821
        if not self._platform and self.platform_id:
            self._platform = PlatformPersistService.retrieve(self.platform_id)
        return self._platform

    @platform.setter
    def platform(self, platform):
        if platform:
            self.platform_id = platform.uid
            self._platform = platform
        else:
            self._platform = self.platform_id = None

    def get_platform_object(self, force=False, **kwargs):
        if not self.platform:
            raise NoPlatformException("The object has no platform set...")

        if self._platform_object is None or force:
            self._platform_object = self.platform.get_item(self.uid, self.item_type, raw=True, force=force, **kwargs)
        return self._platform_object

    @property
    def done(self):
        return self.status in (EntityStatus.SUCCEEDED, EntityStatus.FAILED)

    @property
    def succeeded(self):
        return self.status == EntityStatus.SUCCEEDED

    def __hash__(self):
        return id(self.uid)


IEntityList = List[IEntity]
