"""
Platform Analysis is a wrapper to allow execution of analysis through SSMT vs Locally.

Running remotely has great advantages over local execution with the biggest being more compute resources and less data transfer.
Platform Analysis tries to make the process of running remotely similar to local execution.

Copyright 2025, Bill Gates Foundation. All rights reserved.
"""
import inspect
import os
import pickle
import re
from dataclasses import dataclass, field
from logging import getLogger, DEBUG
from typing import List,  Dict, Callable, Union, Type, Any

from idmtools import IdmConfigParser
from idmtools.analysis.base_analyze_manager import BaseAnalyzeManager
from idmtools.analysis.ianalyze_manager import IAnalysisManager
from idmtools.assets.file_list import FileList
from idmtools.core.interfaces.ientity import IEntity
from idmtools.entities.ianalyzer import IAnalyzer
from idmtools.assets import AssetCollection, Asset
from idmtools.core import ItemType
from idmtools.entities.iplatform_default import AnalyzerManagerPlatformDefault
from idmtools.utils.info import get_help_version_url

logger = getLogger(__name__)
user_logger = getLogger('user')


@dataclass(repr=False)
class PlatformAnalysis(IAnalysisManager, BaseAnalyzeManager):
    """
    PlatformAnalysis allows remote analysis on the server.
    """
    analysis_name: str = field(default="Platform Analysis", metadata=dict(help="Name of the analysis."))
    tags: dict[str, Any] = field(default_factory=dict, metadata=dict(help="Tags for the analysis."))
    additional_files: Union[FileList, AssetCollection, List[str]] = field(default=None, metadata=dict(help="Additional files to include in the analysis."))
    asset_collection_id: str = field(default=None, metadata=dict(help="ID of the asset collection to use."))
    asset_files: Union[FileList, AssetCollection, List[str]] = field(default=None, metadata=dict(help="Asset files to include in the analysis."))
    wait_till_done: bool = field(default=True, metadata=dict(help="If True, wait until the analysis is complete."))
    idmtools_config: str = field(default=None, metadata=dict(help="Path to the idmtools configuration file."))
    pre_run_func: Callable = field(default=None, metadata=dict(help="Function to run before the analysis starts."))
    wrapper_shell_script: str = field(default=None, metadata=dict(help="Path to a wrapper shell script."))

    def __post_init__(self):
        """
        Initialize the PlatformAnalysis object.

        Returns:
            None
        """
        if isinstance(self.additional_files, list):
            additional_files = AssetCollection(self.additional_files)
        elif isinstance(self.additional_files, FileList):
            additional_files = self.additional_files.to_asset_collection()
        else:
            additional_files = self.additional_files  # Default value
        self.additional_files: AssetCollection = additional_files or AssetCollection()

        if isinstance(self.asset_files, list):
            asset_files = AssetCollection(self.asset_files)
        elif isinstance(self.asset_files, FileList):
            asset_files = self.asset_files.to_asset_collection()
        else:
            asset_files = self.asset_files
        self.asset_files: AssetCollection = asset_files or AssetCollection()
        self.wi = None
        self.shell_script_binary = "/bin/bash"
        # Store extra arguments in a dictionary
        self.extra_args: Dict = {
            "partial_analyze_ok": self.partial_analyze_ok,
            "max_items": self.max_items,
            "force_manager_working_directory": self.force_manager_working_directory,
            "exclude_ids": self.exclude_ids,
            "analyze_failed_items": self.analyze_failed_items,
            "max_workers": self.max_workers,
            "executor_type": self.executor_type,
        }

        self.experiment_ids = []  # Initialize empty lists
        self.simulation_ids = []
        self.work_item_ids = []

        if self.ids:
            self._process_ids(self.ids)  # Process initial IDs

    def _process_ids(self, ids):
        """
        Helper method to populate experiment_ids, simulation_ids, and work_item_ids.
        """
        for item_id, item_type in ids:
            if item_type == ItemType.EXPERIMENT:
                self.experiment_ids.append(item_id)
            elif item_type == ItemType.SIMULATION:
                self.simulation_ids.append(item_id)
            elif item_type == ItemType.WORKFLOW_ITEM:
                self.work_item_ids.append(item_id)

    def add_item(self, item: IEntity) -> None:
        """
        Add an item to the list of items to be analyzed.

        Args:
            item: The item to add.
        """
        if item.item_type == ItemType.EXPERIMENT:
            self.experiment_ids.append(item.id)
        elif item.item_type == ItemType.SIMULATION:
            self.simulation_ids.append(item.id)
        elif item.item_type == ItemType.WORKFLOW_ITEM:
            self.work_item_ids.append(item.id)
        else:
            raise ValueError(f"Not support item type: {item.item_type}")

    def add_analyzer(self, analyzer: IAnalyzer) -> None:
        """
        Add an analyzer to the list of analyzers to run.

        Args:
            analyzer: The analyzer to add.
        """
        self.analyzers.append(analyzer)

    def analyze(self) -> bool:
        """
        Run the analysis on the platform.

        Returns:
            True if the analysis was successful, False otherwise.
        """
        # Prepare the command for analysis
        command = self._prep_analyze()

        logger.debug(f"Command: {command}")
        from idmtools_platform_comps.ssmt_work_items.comps_workitems import SSMTWorkItem

        # Create an asset collection
        ac = AssetCollection.from_id(self.asset_collection_id,
                                     platform=self.platform) if self.asset_collection_id else AssetCollection()
        ac.add_assets(self.asset_files)

        # Create the work item
        self.wi = SSMTWorkItem(
            name=self.analysis_name,
            command=command,
            tags=self.tags,
            transient_assets=self.additional_files,
            assets=ac,
            related_experiments=self.experiment_ids,
            related_simulations=self.simulation_ids,
            related_work_items=self.work_item_ids
        )

        # Run the work item
        self.platform.run_items(self.wi)
        if self.wait_till_done:
            self.platform.wait_till_done(self.wi)
        logger.debug(f"Status: {self.wi.status}")

        return self.wi.status == "Succeeded"

    def get_work_item(self):
        """
        Get the work item used to run the analysis job on the server.

        Returns:
            The work item.
        """
        return self.wi

    def _prep_analyze(self) -> str:
        """
        Prepare for analysis.

        Returns:
            The command to run the analysis.
        """
        # Add the platform_analysis_bootstrap.py file to the collection
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.additional_files.add_or_replace_asset(os.path.join(dir_path, "platform_analysis_bootstrap2.py"))

        # Check if user provided an override to idmtools config
        if self.idmtools_config:
            self.additional_files.add_or_replace_asset(self.idmtools_config)
        else:
            # Look for one from idmtools
            config_path = IdmConfigParser.get_config_path()
            if config_path and os.path.exists(config_path):
                if logger.isEnabledFor(DEBUG):
                    logger.debug(f"Adding config file: {config_path}")
                self.additional_files.add_or_replace_asset(config_path)

        if self.pre_run_func:
            self.__pickle_pre_run()

        # Save pickle file as a temp file
        self.__pickle_analyzers(self.analyzers)

        # Add all the analyzers' files
        for a in self.analyzers:
            self.additional_files.add_or_replace_asset(inspect.getfile(a.__class__))

        # Add extra arguments for analyzer manager
        if 'max_workers' not in self.extra_args:
            am_defaults: List[AnalyzerManagerPlatformDefault] = self.platform.get_defaults_by_type(
                AnalyzerManagerPlatformDefault)
            if len(am_defaults):
                if logger.isEnabledFor(DEBUG):
                    logger.debug(f"Setting max workers to comps default of: {am_defaults[0].max_workers}")
                self.extra_args['max_workers'] = am_defaults[0].max_workers

        # Create the command
        command = ''
        if self.wrapper_shell_script:
            self.additional_files.add_or_replace_asset(self.wrapper_shell_script)
            command += f'{self.shell_script_binary} {os.path.basename(self.wrapper_shell_script)} '
        command += "python3 platform_analysis_bootstrap2.py"

        # Add the experiments, simulations, and work items
        if self.experiment_ids:
            command += f' --experiment-ids {",".join(self.experiment_ids)}'
        if self.simulation_ids:
            command += f' --simulation-ids {",".join(self.simulation_ids)}'
        if self.work_item_ids:
            command += f' --work-item-ids {",".join(self.work_item_ids)}'

        # Add the analyzers
        command += " --analyzers {}".format(
            ",".join(
                f"{inspect.getmodulename(inspect.getfile(a.__class__))}.{a.__class__.__name__}"
                for a in self.analyzers
            )
        )

        if self.pre_run_func:
            command += f" --pre-run-func {self.pre_run_func.__name__}"

        # Pickle the extra args
        if len(self.extra_args):
            from idmtools.analysis.analyze_manager2 import AnalyzeManager
            argspec = inspect.signature(AnalyzeManager.__init__)
            for argname, value in self.extra_args.items():
                if argname not in argspec.parameters:
                    raise ValueError(
                        f"AnalyzerManager does not support the argument {argname}. Valid args are {' '.join([str(s) for s in argspec.parameters.keys()])}. See {get_help_version_url('idmtools.analysis.analyze_manager.html#idmtools.analysis.analyze_manager.AnalyzeManager')} for a valid list of arguments.")
            self.additional_files.add_or_replace_asset(
                Asset(filename="extra_args.pkl", content=pickle.dumps(self.extra_args)))
            command += " --analyzer-manager-args-file extra_args.pkl"

        # Add platform
        ssmt_config_block = f"{self.platform.config_block}_SSMT"
        command += " --block {}".format(ssmt_config_block)
        if self.verbose:
            command += " --verbose"

        return command

    def __pickle_analyzers(self, analyzers: List[Type[IAnalyzer]]):
        """
        Pickle our analyzers and add as assets.

        Args:
            analyzers: Analyzer instances

        Returns:
            None
        """
        # Create a list of dictionaries containing class name and configuration
        analyzer_data = []
        for analyzer in analyzers:
            # Get __init__ method parameters (excluding self)
            init_params = inspect.signature(analyzer.__init__).parameters
            init_param_names = {param for param in init_params if param != "self"}

            # Extract only the parameters defined in __init__
            config = {}
            for param in init_param_names:
                if param in analyzer.__dict__:
                    config[param] = analyzer.__dict__[param]  # Direct match
                elif f"_{param}" in analyzer.__dict__:  # match with underscore in __init__
                    config[param] = analyzer.__dict__[f"_{param}"]

            analyzer_data.append({
                "module_name": analyzer.__class__.__module__.split(".")[-1],  # Save the only module name
                "class_name": analyzer.__class__.__name__,  # Save only the class name
                "config": config  # Save only relevant parameters
            })

        # Save to pickle file
        self.additional_files.add_or_replace_asset(Asset(filename='analyzers.pkl', content=pickle.dumps(analyzer_data)))

    def __pickle_pre_run(self):
        """
        Pickle objects before we run and add items as assets.

        Returns:
            None
        """
        source = inspect.getsource(self.pre_run_func).splitlines()
        space_base = 0
        while source[0][space_base] == " ":
            space_base += 1
        replace_expr = re.compile("^[ ]{" + str(space_base) + "}")
        new_source = []
        for line in source:
            new_source.append(replace_expr.sub("", line))

        self.additional_files.add_or_replace_asset(Asset(filename="pre_run.py", content="\n".join(new_source)))
