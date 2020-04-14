import typing
from abc import ABC
from dataclasses import dataclass, field

from idmtools.core.interfaces.inamed_entity import INamedEntity
from idmtools.core import ItemType, EntityContainer

if typing.TYPE_CHECKING:
    from typing import NoReturn


@dataclass(repr=False)
class Suite(INamedEntity, ABC):
    """
    Class that represents a generic suite (a collection of experiments).

    Args:
        experiments: The child items of this suite.
    """
    experiments: 'EntityContainer' = field(default_factory=lambda: EntityContainer(), compare=False,
                                           metadata={"pickle_ignore": True})

    item_type: 'ItemType' = field(default=ItemType.SUITE, compare=False, init=False)
    description: str = field(default=None, compare=False)

    def add_experiment(self, experiment: 'Experiment') -> 'NoReturn':  # noqa: F821
        """
        Add an experiment to the suite
        Args:
            experiment: the experiment to be linked to suite
        """
        # Link the suite to the experiment
        experiment.suite = self

        # Add the experiment to the list
        self.experiments.append(experiment)

    def display(self):
        from idmtools.utils.display import display, suite_table_display
        display(self, suite_table_display)

    def pre_creation(self):
        pass

    def post_creation(self):
        pass

    def __repr__(self):
        return f"<Suite {self.uid} - {len(self.experiments)} experiments>"


ISuiteClass = typing.Type[Suite]
