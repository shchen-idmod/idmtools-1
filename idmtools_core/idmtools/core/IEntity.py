import typing
from abc import ABCMeta

from idmtools.utils.hashing import hash_obj
from idmtools.core import IPicklableObject

if typing.TYPE_CHECKING:
    import uuid
    from idmtools.core import TTags


class IEntity(IPicklableObject, metaclass=ABCMeta):
    """
    Interface for all entities in the system.
    """
    def __init__(self, uid: 'uuid' = None, tags: 'TTags' = None):
        super().__init__()
        self._uid = uid
        self.tags = tags or {}
        self.platform_id = None

    @property
    def uid(self):
        return self._uid or hash_obj(self)

    @uid.setter
    def uid(self, uid):
        self._uid = uid

    # region Events methods
    def pre_creation(self) -> None:
        """
        Called before the actual creation of the entity.
        """
        pass

    def post_creation(self) -> None:
        """
        Called after the actual creation of the entity.
        """
        pass
    # endregion

