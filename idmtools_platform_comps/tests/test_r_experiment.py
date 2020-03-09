import os
import sys
from unittest import TestCase
import pytest
from idmtools_models.r.json_r_task import JSONConfiguredRTask
from idmtools_models.r.r_task import RTask
from idmtools_test import COMMON_INPUT_PATH

from idmtools.core.platform_factory import Platform
from idmtools.entities.command_task import CommandTask
from idmtools.entities.experiment import Experiment
from idmtools.assets import AssetCollection
from idmtools_test.utils.itest_with_persistence import ITestWithPersistence
from idmtools.assets.file_list import FileList
from idmtools_platform_comps.ssmt_work_items.comps_workitems import SSMTWorkItem


@pytest.mark.tasks
@pytest.mark.r
class TestRExperiment(ITestWithPersistence):

    def setUp(self) -> None:
        self.platform = Platform('COMPS2')
        self.case_name = os.path.basename(__file__) + "--" + self._testMethodName
        self.input_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inputs")

    def validate_common_assets(self, fpath, task):
        """
        Validate common assets on a R task

        Args:
            fpath: Source path to model file
            task: Task object to validate

        Returns:
            None
        """
        self.assertEqual(len(task.common_assets.assets), 1, f'Asset list is: {[str(x) for x in task.common_assets.assets]}')
        self.assertEqual(task.common_assets.assets[0].absolute_path, fpath)

    @pytest.mark.skip
    def test_json_r_static_filename_no_argument_commission(self):
        fpath = os.path.join(COMMON_INPUT_PATH, "r", "ncov_analysis", "individual_dynamics_estimates",
                             "estimate_incubation_period.R")
        # task = JSONConfiguredRTask(script_name=fpath, configfile_argument=None, image_name='r-base:3.6.1')
        command = "RScript ./Assets/estimate_incubation_period.R"
        task = CommandTask(command=command)

        task.gather_all_assets()

        # self.assertEqual(str(task.command), f'Rscript ./Assets/estimate_incubation_period.R')
        self.validate_common_assets(fpath, task)
        self.validate_json_transient_assets(task)

        ac_lib_path = os.path.join(COMMON_INPUT_PATH, "r", "ncov_analysis")

        # Create AssetCollection from dir to provide to the Experiment task
        r_model_assets = AssetCollection.from_directory(assets_directory=ac_lib_path, flatten=False,
                                                              relative_path="ncov_analysis")

        experiment = Experiment.from_task(task, name="test_r_task.py--test_r_model_with_ac",
                                          assets=r_model_assets)

        platform = Platform('HPC_LINUX')
        platform.run_items(experiment)
        platform.wait_till_done(experiment)

        # Check experiment status, only move to Analyzer step if experiment succeeded.
        if not experiment.succeeded:
            print(f"Experiment {experiment.uid} failed.\n")
            sys.exit(-1)

    @pytest.mark.skip
    def test_r_model_w_ac_no_args(self):
        fpath = os.path.join(COMMON_INPUT_PATH, "r", "ncov_analysis", "individual_dynamics_estimates",
                             "estimate_incubation_period.R")
        task = JSONConfiguredRTask(script_name=fpath, configfile_argument=None, image_name='r-base:3.6.1')
        task.gather_all_assets()

        self.assertEqual(str(task.command),
                         f'Rscript ./Assets/estimate_incubation_period.R')
        self.validate_common_assets(fpath, task)
        self.validate_json_transient_assets(task)

        ac_lib_path = os.path.join(COMMON_INPUT_PATH, "r", "ncov_analysis")

        # Create AssetCollection from dir to provide to the Experiment task
        ncov_analysis_assets = AssetCollection.from_directory(assets_directory=ac_lib_path, flatten=False,
                                                              relative_path="ncov_analysis")

        experiment = Experiment.from_task(task, name="test_r_task.py--test_r_model_with_ac",
                                          assets=ncov_analysis_assets)

        platform = Platform('HPC_LINUX')
        platform.run_items(experiment)
        platform.wait_till_done(experiment)

        # Check experiment status, only move to Analyzer step if experiment succeeded.
        if not experiment.succeeded:
            print(f"Experiment {experiment.uid} failed.\n")
            sys.exit(-1)

    @pytest.mark.skip
    def test_r_model_with_load_ac(self):
        # Utility does not support R libraries only Python packages at this time
        platform = Platform('COMPS2')

        ac_lib_path = os.path.join(COMMON_INPUT_PATH, "r", "ncov_analysis")

        # Create AssetCollection from dir to provide to the Experiment task
        ncov_analysis_assets = AssetCollection.from_directory(assets_directory=ac_lib_path, flatten=False,
                                                              relative_path="ncov_analysis")

        command = "RScript Assets/ncov_analysis/individual_dynamics_estimates/estimate_incubation_period.R"
        task = CommandTask(command=command)

        # model_asset = os.path.join(COMMON_INPUT_PATH, "r", "ncov_analysis", "individual_dynamics_estimates",
        #                            "estimate_incubation_period.R")

        # task = JSONConfiguredRTask(script_name=fpath, configfile_argument=None, common_assets=ncov_analysis_assets)

        experiment = Experiment.from_task(task, name="test_r_task.py--test_r_model_with_ac",
                                          assets=ncov_analysis_assets)
        # experiment.assets.add_directory(ac_lib_path)

        platform.run_items(experiment)
        platform.wait_till_done(experiment)

        # Check experiment status, only move to Analyzer step if experiment succeeded.
        if not experiment.succeeded:
            print(f"Experiment {experiment.uid} failed.\n")
            sys.exit(-1)

    @pytest.mark.skip
    # TODO: need correct RScript path
    def test_r_ssmt_workitem_add_ac_from_path(self):
        ac_lib_path = os.path.join(COMMON_INPUT_PATH, "r", "ncov_analysis")

        # load assets to COMPS's assets
        asset_files = FileList()
        asset_files.add_path(ac_lib_path, relative_path="ncov_analysis", recursive=True)

        # load local "input" foleer simtools.ini to current dir in Comps workitem
        user_files = FileList()
        user_files.add_file(os.path.join(self.input_file_path, "idmtools.ini"))

        self.tags = {'idmtools': self._testMethodName, 'WorkItem type': 'Docker'}
        command = "/usr/bin/Rscript estimate_incubation_period.R"
        wi = SSMTWorkItem(item_name=self.case_name, command=command, asset_files=asset_files, user_files=user_files,
                          tags=self.tags, docker_image="ubuntu1804_r")
        wi.run(True, platform=self.platform)
