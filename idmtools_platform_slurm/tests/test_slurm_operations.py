import os
from functools import partial
import pytest
from idmtools.builders import SimulationBuilder
from idmtools.core import ItemType, EntityStatus

from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
from idmtools_models.python.json_python_task import JSONConfiguredPythonTask
from idmtools_test import COMMON_INPUT_PATH
from idmtools_test.utils.decorators import linux_only
from idmtools_test.utils.itest_with_persistence import ITestWithPersistence

from idmtools.entities.templated_simulation import TemplatedSimulations

from idmtools_platform_slurm.platform_operations.utils import add_dammy_suite, SlurmExperiment, SlurmSimulation

setA = partial(JSONConfiguredPythonTask.set_parameter_sweep_callback, param="a")

@pytest.mark.serial
@linux_only
class TestSlurmOperations(ITestWithPersistence):

    def create_experiment(self, platform=None):
        task = JSONConfiguredPythonTask(script_path=os.path.join(COMMON_INPUT_PATH, 'python', 'model1.py'),
                                      parameters=dict(c='c-value'))
        task.common_assets.add_asset('input/hello.sh')
        ts = TemplatedSimulations(base_task=task)
        builder = SimulationBuilder()
        builder.add_sweep_definition(setA, range(0, 2))
        ts.add_builder(builder)
        exp = Experiment(name=self.case_name, simulations=ts, tags=dict(number_tag=123, KeyOnly=None))
        suite = add_dammy_suite(exp)
        suite.run(platform=platform, wait_until_done=False, wait_on_done=False, dry_run=False)
        return suite, exp

    def setUp(self) -> None:
        self.case_name = os.path.basename(__file__) + '--' + self._testMethodName
        self.job_directory = 'DEST'
        self.platform = Platform('SLURM_LOCAL', job_directory=self.job_directory)
        self.suite, self.exp = self.create_experiment(self.platform)

    def test_retrieve_experiment(self):
        exp = self.platform.get_item(self.exp.uid, ItemType.EXPERIMENT)
        # Test attributes
        self.assertEqual(self.exp.uid, exp.uid)
        self.assertEqual(self.exp.name, exp.name)

        # Comps returns tags as string regardless of type
        self.assertEqual({k: (v or None) for k, v in self.exp.tags.items()}, exp.tags)

        # Test the raw retrieval
        slurm_experiment = self.platform.get_item(self.exp.uid, ItemType.EXPERIMENT, raw=True)
        self.assertIsInstance(slurm_experiment, SlurmExperiment)
        self.assertEqual(str(self.exp.uid), slurm_experiment.uid)
        self.assertEqual(self.exp.name, slurm_experiment.name)
        self.assertEqual({k: (v or None) for k, v in self.exp.tags.items()}, slurm_experiment.tags)

        # Test retrieving less columns. Note, we still retrieve ONLY by uid, columns does not apply in filter
        tags = {'number_tag': 456}
        slurm_experiment = self.platform.get_item(self.exp.uid, ItemType.EXPERIMENT, raw=True, load_children=[],
                                                  columns=[tags])
        self.assertEqual(str(self.exp.uid), slurm_experiment.uid)
        self.assertEqual(self.exp.name, slurm_experiment.name)
        self.assertEqual(str(self.exp.uid), slurm_experiment.uid)

    def test_retrieve_simulation(self):
        base = self.exp.simulations[0]
        sim = self.platform.get_item(base.uid, ItemType.SIMULATION)
        # Test attributes
        self.assertEqual(sim.uid, base.uid)
        self.assertEqual(sim.name, base.name)
        self.assertEqual({k: v for k, v in base.tags.items()}, sim.tags)

        # Test the raw retrieval
        slurm_simulation: SlurmSimulation = self.platform.get_item(base.uid, ItemType.SIMULATION, raw=True)
        self.assertIsInstance(slurm_simulation, SlurmSimulation)
        self.assertEqual(str(base.uid), slurm_simulation.uid)
        self.assertEqual(self.case_name, slurm_simulation.name)
        self.assertEqual({k: v for k, v in base.tags.items()}, slurm_simulation.tags)

    def test_parent(self):
        parent_exp = self.platform.get_parent(self.exp.simulations[0].uid, ItemType.SIMULATION)
        self.assertEqual(self.exp.uid, parent_exp.uid)
        self.assertEqual({k: v or None for k, v in self.exp.tags.items()}, parent_exp.tags)
        parent_suite = self.platform.get_parent(self.exp.uid, ItemType.EXPERIMENT)
        self.assertEqual(self.suite.uid, parent_suite.uid)

    def test_children(self):
        children = self.platform.get_children(self.exp.uid, ItemType.EXPERIMENT)
        self.assertEqual(len(self.exp.simulations), len(children))
        for s in self.exp.simulations:
            self.assertIn(s.uid, [s.uid for s in children])
        self.assertCountEqual(self.platform.get_children(self.exp.simulations[0].uid, ItemType.SIMULATION), [])

    def test_experiment_list_assets(self):
        with self.subTest('test_list_assets'):
            assets = self.platform._experiments.list_assets(self.exp)
            self.assertEqual(2, len(assets))
            self.assertEqual('model1.py', assets[0].filename)
            self.assertEqual('hello.sh', assets[1].filename)
            experiment_dir = self.platform._op_client.get_directory(self.exp).resolve()
            self.assertEqual(assets[0].absolute_path, experiment_dir.joinpath('Assets/model1.py'))
            self.assertEqual(assets[1].absolute_path, experiment_dir.joinpath('Assets/hello.sh'))
        with self.subTest('test_list_assets_add_exclude'):
            assets = self.platform._experiments.list_assets(self.exp, exclude='hello.sh')
            self.assertEqual(1, len(assets))
            self.assertEqual('model1.py', assets[0].filename)

    def test_simulation_list_assets(self):
        count = 0
        for sim in self.exp.simulations:
            assets = self.platform._simulations.list_assets(sim)
            self.assertEqual(1, len(assets))
            self.assertEqual('config.json', assets[0].filename)
            simulation_dir = self.platform._op_client.get_directory(sim).resolve()
            self.assertEqual(assets[0].absolute_path, simulation_dir.joinpath('config.json'))
            count += 1
        self.assertEqual(count, 2)

    def test_platform_list_files(self):
        assets = self.platform._experiments.platform_list_files(self.exp)
        self.assertEqual(len(assets), 2)

    def test_to_entity(self):
        slurm_experiment = self.platform.get_item(self.exp.id, item_type=ItemType.EXPERIMENT, raw=True)
        idm_experiment = self.platform._experiments.to_entity(slurm_experiment)
        self.assertEqual(slurm_experiment.id, idm_experiment.id)
        self.assertEqual(slurm_experiment.uid, idm_experiment.id)
        self.assertEqual(slurm_experiment.name, idm_experiment.name)
        self.assertEqual(slurm_experiment.tags, idm_experiment.tags)
        self.assertEqual(sorted(slurm_experiment.simulations),sorted([sim.id for sim in idm_experiment.simulations.items]))

        # we only compare asset filenames
        slurm_experiment_assets = [asset['filename'] for asset in slurm_experiment.assets]
        idm_experiment_assets = [asset.filename for asset in idm_experiment.assets]
        self.assertEqual(sorted(slurm_experiment_assets), sorted(idm_experiment_assets))
        self.assertEqual(slurm_experiment.status, 'CREATED')
        self.assertEqual(idm_experiment.status, EntityStatus.CREATED)
