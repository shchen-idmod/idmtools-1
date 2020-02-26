import os
import unittest
from functools import partial

import pytest
from COMPS.Data import Experiment as COMPSExperiment, Simulation as COMPSSimulation

from idmtools.builders import SimulationBuilder
from idmtools.core import ItemType
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
from idmtools.entities.templated_simulation import TemplatedSimulations
from idmtools_models.python.json_python_task import JSONConfiguredPythonTask
from idmtools_test import COMMON_INPUT_PATH
from idmtools_test.utils.itest_with_persistence import ITestWithPersistence

setA = partial(JSONConfiguredPythonTask.set_parameter_sweep_callback, param="a")


@pytest.mark.comps
class TestRetrieval(ITestWithPersistence):
    @classmethod
    def setUpClass(cls) -> None:
        cls.case_name = os.path.basename(__file__) + "--" + cls.__name__
        print(cls.case_name)

        cls.platform = Platform('COMPS2')
        print(cls.platform.uid)
        bt = JSONConfiguredPythonTask(script_path=os.path.join(COMMON_INPUT_PATH, "python", "model1.py"),
                                      parameters=dict(c="c-value"))
        ts = TemplatedSimulations(base_task=bt)
        builder = SimulationBuilder()
        builder.add_sweep_definition(setA, range(0, 2))
        ts.add_builder(builder)
        cls.pe = Experiment(name=cls.case_name, simulations=ts,
                            tags=dict(string_tag="test", number_tag=123, KeyOnly=None))

        cls.platform.run_items(cls.pe)
        cls.platform.wait_till_done(cls.pe)

    def test_retrieve_experiment(self):
        exp = self.platform.get_item(self.pe.uid, ItemType.EXPERIMENT)

        # Test attributes
        self.assertEqual(self.pe.uid, exp.uid)
        self.assertEqual(self.pe.name, exp.name)

        # Comps returns tags as string regardless of type
        self.assertEqual({k: str(v or '') for k, v in self.pe.tags.items()}, exp.tags)

        # Test the raw retrieval
        comps_experiment = self.platform.get_item(self.pe.uid, ItemType.EXPERIMENT, raw=True)
        self.assertIsInstance(comps_experiment, COMPSExperiment)
        self.assertEqual(self.pe.uid, comps_experiment.id)
        self.assertEqual(self.pe.name, comps_experiment.name)
        self.assertEqual({k: str(v or '') for k, v in self.pe.tags.items()}, comps_experiment.tags)

        # Test retrieving less columns
        comps_experiment = self.platform.get_item(self.pe.uid, ItemType.EXPERIMENT, raw=True, children=[],
                                                  columns=["id"])
        self.assertIsNone(comps_experiment.name)
        self.assertIsNone(comps_experiment.tags)
        self.assertEqual(self.pe.uid, comps_experiment.id)

    @unittest.skip
    def test_retrieve_simulation(self):
        base = self.pe.simulations[0]
        sim = self.platform.get_item(base.uid, ItemType.SIMULATION)

        # Test attributes
        self.assertEqual(sim.uid, base.uid)
        self.assertEqual(sim.name, base.name)
        self.assertEqual({k: str(v or '') for k, v in base.tags.items()}, sim.tags)

        # Test the raw retrieval
        comps_simulation: COMPSSimulation = self.platform.get_item(base.uid, ItemType.SIMULATION, raw=True)
        self.assertIsInstance(comps_simulation, COMPSSimulation)
        self.assertEqual(base.uid, comps_simulation.id)
        self.assertEqual(base.name, comps_simulation.name)
        self.assertEqual({k: str(v or '') for k, v in base.tags.items()}, comps_simulation.tags)

    def test_parent(self):
        parent_exp = self.platform.get_parent(self.pe.simulations[0].uid, ItemType.SIMULATION)
        self.assertEqual(self.pe.uid, parent_exp.uid)
        self.assertEqual({k: str(v or '') for k, v in self.pe.tags.items()}, parent_exp.tags)
        self.assertIsNone(self.platform.get_parent(self.pe.uid, ItemType.EXPERIMENT))

    def test_children(self):
        children = self.platform.get_children(self.pe.uid, ItemType.EXPERIMENT)
        self.assertEqual(len(self.pe.simulations), len(children))
        for s in self.pe.simulations:
            self.assertIn(s.uid, [s.uid for s in children])
        self.assertCountEqual(self.platform.get_children(self.pe.simulations[0].uid, ItemType.SIMULATION), [])


if __name__ == '__main__':
    unittest.main()
