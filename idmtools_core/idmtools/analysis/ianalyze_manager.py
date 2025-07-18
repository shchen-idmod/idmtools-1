"""
This module contains the interface for analysis management classes.
"""
from abc import ABC, abstractmethod
from idmtools.core.interfaces.ientity import IEntity
from idmtools.entities.ianalyzer import IAnalyzer


class IAnalysisManager(ABC):
    """
    Interface for analysis management classes.
    """

    @abstractmethod
    def add_item(self, item: IEntity) -> None:
        """
        Add an item to the list of items to be analyzed.

        Args:
            item: The item to add.
        """
        pass

    @abstractmethod
    def add_analyzer(self, analyzer: IAnalyzer) -> None:
        """
        Add an analyzer to the list of analyzers to run.

        Args:
            analyzer: The analyzer to add.
        """
        pass

    @abstractmethod
    def analyze(self) -> bool:
        """
        Run the analysis.

        Returns:
            True if the analysis was successful, False otherwise.
        """
        pass
