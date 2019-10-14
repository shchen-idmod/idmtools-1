import typing
from abc import ABC
from dataclasses import dataclass, field
from idmtools.core.interfaces.inamed_entity import INamedEntity

if typing.TYPE_CHECKING:
    from idmtools.entities.iexperiment import TExperimentList


@dataclass(repr=False)
class ISuite(INamedEntity, ABC):
    """
    Represents a generic Suite (of experiments).

    Args:
        experiments: the children items of this suite
    """
    experiments: 'TExperimentList' = field(default=None, compare=False, metadata={"md": True})


TSuite = typing.TypeVar("TSuite", bound=ISuite)
