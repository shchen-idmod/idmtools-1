import os
import sys
from unittest import TestCase
import pytest
from idmtools.builders import SimulationBuilder
from idmtools.core import EntityStatus
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
from idmtools.entities.simulation import Simulation
from idmtools_models.python.json_python_task import JSONConfiguredPythonTask
from idmtools_models.python.python_task import PythonTask
from idmtools_test import COMMON_INPUT_PATH


@pytest.mark.tasks
class TestPythonTask(TestCase):

    @pytest.mark.smoke
    def test_simple_model(self):
        fpath = os.path.join(COMMON_INPUT_PATH, "python", "model1.py")
        task = PythonTask(script_path=fpath)
        task.gather_all_assets()

        self.assertEqual(str(task.command), f'python ./Assets/model1.py')
        self.validate_common_assets(fpath, task)

    def validate_common_assets(self, fpath, task):
        """
        Validate common assets on a python model

        Args:
            fpath: Source path to model file
            task: Task object to validate

        Returns:
            None
        """
        self.assertEqual(len(task.common_assets.assets), 1, f'Asset list is: {[str(x) for x in task.common_assets.assets]}')
        self.assertEqual(task.common_assets.assets[0].absolute_path, fpath)

    def validate_json_transient_assets(self, task, config_file_name='config.json'):
        """
        Validate JSON Python task has correct transient assets
        Args:
            task: Task to validate
            config_file_name: Files name the json config should be. Default to config.json
        Returns:

        """
        self.assertEqual(len(task.transient_assets.assets), 1)
        self.assertEqual(task.transient_assets.assets[0].filename, config_file_name)

    def test_json_python_argument(self):
        fpath = os.path.join(COMMON_INPUT_PATH, "python", "model1.py")
        task = JSONConfiguredPythonTask(script_path=fpath)
        task.gather_all_assets()

        self.assertEqual(str(task.command), f'python ./Assets/model1.py --config config.json')
        self.validate_common_assets(fpath, task)
        self.validate_json_transient_assets(task)

    def test_json_python_static_filename_no_argument(self):
        fpath = os.path.join(COMMON_INPUT_PATH, "python", "model1.py")
        # here we test a script that may have no configu
        task = JSONConfiguredPythonTask(script_path=fpath, configfile_argument=None)
        task.gather_all_assets()

        self.assertEqual(str(task.command), f'python ./Assets/model1.py')
        self.validate_common_assets(fpath, task)
        self.validate_json_transient_assets(task)

    def test_different_python_path(self):
        fpath = os.path.join(COMMON_INPUT_PATH, "python", "model1.py")
        task = JSONConfiguredPythonTask(script_path=fpath, configfile_argument=None, python_path='python3.8')
        task.gather_all_assets()

        self.assertEqual(str(task.command), f'python3.8 ./Assets/model1.py')
        self.validate_common_assets(fpath, task)
        self.validate_json_transient_assets(task)

    @pytest.mark.smoke
    def test_model1(self):
        with Platform("TestExecute", missing_ok=True, default_missing=dict(type='TestExecute')):
            fpath = os.path.join(COMMON_INPUT_PATH, "python", "model1.py")
            # here we test a script
            params = dict(a=1, b=2, c=3)
            task = JSONConfiguredPythonTask(
                script_path=fpath,
                configfile_argument=None,
                python_path=sys.executable,
                parameters=params
            )
            experiment = Experiment.from_task(task)
            experiment.run(True)

            self.assertTrue(experiment.succeeded)
            self.assertEqual(1, experiment.simulation_count)
            self.assertEqual(EntityStatus.SUCCEEDED, experiment.simulations[0].status)

            with self.subTest("reload_simulation"):
                experiment_reload = Experiment.from_id(experiment.uid, load_task=True)
                self.assertEqual(experiment.id, experiment_reload.id)
                self.assertEqual(experiment.simulation_count, experiment_reload.simulation_count)
                self.assertEqual(experiment.succeeded, experiment_reload.succeeded)
                sim1: Simulation = experiment_reload.simulations[0]
                self.assertEqual(experiment.simulations[0].uid, sim1.uid)
                self.assertEqual(0, sim1.assets.count)
                self.assertEqual(experiment.simulations[0].task.command, sim1.task.command)
                self.assertEqual(params, sim1.task.parameters)

    @pytest.mark.smoke
    def test_model_sweep(self):
        with Platform("TestExecute", missing_ok=True, default_missing=dict(type='TestExecute')):
            fpath = os.path.join(COMMON_INPUT_PATH, "python", "model1.py")
            # here we test a script that may have no config
            task = JSONConfiguredPythonTask(script_path=fpath, configfile_argument=None, python_path=sys.executable)
            builder = SimulationBuilder()
            builder.add_sweep_definition(task.set_parameter_partial("a"), range(2))
            builder.add_sweep_definition(task.set_parameter_partial("b"), range(2))
            experiment = Experiment.from_builder(builder, base_task=task)
            experiment.run(True)

            self.assertEqual(True, experiment.succeeded)
            self.assertEqual(4, experiment.simulation_count)
            self.assertEqual(EntityStatus.SUCCEEDED, experiment.simulations[0].status)


