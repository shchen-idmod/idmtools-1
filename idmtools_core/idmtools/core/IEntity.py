import uuid
from abc import ABCMeta

from idmtools.utils.hashing import hash_obj


class IEntity(metaclass=ABCMeta):
    """
    Interface for all entities in the system.
    """
    pickle_ignore_fields = []

    def __init__(self, uid: uuid = None, tags: dict = None):
        self._uid = uid
        self.tags = tags or {}
        self.platform_id = None

    @property
    def uid(self):
        return self._uid or hash_obj(self)

    @uid.setter
    def uid(self, uid):
        self._uid = uid

    def __getstate__(self):
        """
        Ignore the fields in pickle_ignore_fields during pickling.
        """
        state = self.__dict__.copy()
        # Don't pickle baz
        for f in self.pickle_ignore_fields:
            del state[f]

        return state

    def __setstate__(self, state):
        """
        Add ignored fields back since they don't exist in the pickle
        """
        self.__dict__.update(state)
        for f in self.pickle_ignore_fields:
            setattr(self, f, None)

    def __eq__(self, other):
        return hash_obj(self) == hash_obj(other)