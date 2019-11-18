import typing
from abc import ABCMeta
from dataclasses import dataclass, field

from idmtools.core import EntityStatus, ItemType, NoPlatformException
from idmtools.core.interfaces.iitem import IItem
from idmtools.services.platforms import PlatformPersistService

if typing.TYPE_CHECKING:
    from idmtools.core import TTags
    from idmtools.entities.iplatform import TPlatform
    from uuid import UUID
    from typing import NoReturn


@dataclass
class IEntity(IItem, metaclass=ABCMeta):
    """
    Interface for all entities in the system.
    """
    platform_id: 'UUID' = field(default=None, compare=False, metadata={"md": True})
    _platform: 'TPlatform' = field(default=None, compare=False, metadata={"pickle_ignore": True})
    parent_id: 'UUID' = field(default=None, metadata={"md": True})
    _parent: 'IEntity' = field(default=None, compare=False, metadata={"pickle_ignore": True})
    status: 'EntityStatus' = field(default=None, compare=False, metadata={"pickle_ignore": True})
    tags: 'TTags' = field(default_factory=lambda: {}, metadata={"md": True})
    item_type: 'ItemType' = field(default=None, compare=False)

    def update_tags(self, tags: 'dict' = None) -> 'NoReturn':
        """
        Shortcut to update the tags with the given dictionary
        Args:
            tags: New tags
        """
        self.tags.update(tags)

    def post_creation(self) -> None:
        self.status = EntityStatus.CREATED

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
    def platform(self):
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

        return self.platform.get_item(self.uid, self.item_type, raw=True, force=force, **kwargs)

    @property
    def done(self):
        return self.status in (EntityStatus.SUCCEEDED, EntityStatus.FAILED)

    @property
    def succeeded(self):
        return self.status == EntityStatus.SUCCEEDED

    def __hash__(self):
        return id(self.uid)


TEntity = typing.TypeVar("TEntity", bound=IEntity)
TEntityList = typing.List[TEntity]