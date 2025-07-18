"""
Analyze Manager Base Class which contains the basic attributes for the analysis manager.
"""
from dataclasses import field, dataclass
from typing import List, Tuple, Optional
from idmtools.entities.iplatform import IPlatform
from idmtools.core.enums import ItemType
from idmtools.entities.ianalyzer import IAnalyzer


@dataclass
class BaseAnalyzeManager:
    """
    Base class for analysis manager.
    """
    platform: IPlatform = field(default=None, metadata=dict(help="Platform to use for analysis."))
    configuration: dict = field(default=None, metadata=dict(help="Configuration for the analysis."))
    ids: List[Tuple[str, ItemType]] = field(default_factory=list, metadata=dict(help="List of items to analyze."))
    analyzers: List[IAnalyzer] = field(default_factory=list, metadata=dict(help="List of analyzers."))
    partial_analyze_ok: bool = field(default=False, metadata=dict(help="Allow partial analysis."))
    max_items: Optional[int] = field(default=None, metadata=dict(help="Maximum number of items to analyze."))
    verbose: bool = field(default=False, metadata=dict(help="Enable verbose logging."))
    force_manager_working_directory: bool = field(default=False, metadata=dict(
        help="Force the use of the manager's working directory."))
    exclude_ids: List[str] = field(default_factory=list,
                                   metadata=dict(help="List of item IDs to exclude from analysis."))
    analyze_failed_items: bool = field(default=False, metadata=dict(help="Allow to analyze failed items."))
    max_workers: Optional[int] = field(default=None,
                                       metadata=dict(help="Maximum number of workers for parallel processing."))
    executor_type: str = field(default='process',
                               metadata=dict(help="Type of executor to use ('process' or 'thread')."))
