import typing
from abc import ABCMeta
from dataclasses import dataclass, field, fields, _MISSING_TYPE
from idmtools.utils.hashing import hash_obj

if typing.TYPE_CHECKING:
    import uuid
    from idmtools.core import TTags


@dataclass(unsafe_hash=True)
class IEntity(metaclass=ABCMeta):
    """
    Interface for all entities in the system.
    """
    _uid: 'uuid' = field(default=None, metadata={"md": True})
    platform_id: int = field(default=None, metadata={"md": True})
    tags: 'TTags' = field(default_factory=lambda: {}, metadata={"md": True})

    @property
    def metadata(self):
        attrs = set(vars(self).keys())
        obj_dict = {k: getattr(self, k) for k in attrs.intersection(self.metadata_fields)}
        return self.__class__(**obj_dict)

    @property
    def pickle_ignore_fields(self):
        return set(f.name for f in fields(self) if "pickle_ignore" in f.metadata and f.metadata["pickle_ignore"])

    @property
    def metadata_fields(self):
        return set(f.name for f in fields(self) if "md" in f.metadata and f.metadata["md"])

    @property
    def uid(self):
        return hash_obj(self) if self._uid is None else self._uid

    @uid.setter
    def uid(self, uid):
        self._uid = uid

    def display(self):
        return self.__repr__()

    # region Events methods
    def pre_creation(self) -> None:
        """
        Call before the actual creation of the entity.
        """
        pass

    def post_creation(self) -> None:
        """
        Call after the actual creation of the entity.
        """
        pass

    def post_setstate(self):
        """
        Call after restoring the state if additional initialization is required.
        """
        pass

    def pre_getstate(self):
        """
        Call before picking to return default values for :meth:`pickle_ignore_fields`.
        """
        pass

    # endregion

    # region State management
    def __getstate__(self):
        """
        Ignore the fields in :meth:`pickle_ignore_fields` during pickling.
        """
        state = self.__dict__.copy()
        attrs = set(vars(self).keys())

        # Retrieve fields default values
        fds = fields(self)
        field_default = {f.name: f.default for f in fds}

        # Update default with parent's pre-populated values
        pre_state = self.pre_getstate()
        pre_state = pre_state or {}
        field_default.update(pre_state)

        # Don't pickle ignore_pickle fields: set values to default
        for field_name in attrs.intersection(self.pickle_ignore_fields):
            if field_name in state:
                if isinstance(field_default[field_name], _MISSING_TYPE):
                    state[field_name] = None
                else:
                    state[field_name] = field_default[field_name]

        return state

    def __setstate__(self, state):
        """
        Add ignored fields back since they don't exist in the pickle.
        """
        self.__dict__.update(state)

        # Restore the pickle fields with values requested
        self.post_setstate()
    # endregion
