import os
import numpy as np
from functools import partial
from idmtools.builders import ArmExperimentBuilder, ArmType, SweepArm
from idmtools.builders import YamlExperimentBuilder
from idmtools.builders import CsvExperimentBuilder
from tests.utils.ITestWithPersistence import ITestWithPersistence
from tests.utils.TestExperiment import TestExperiment
from tests import INPUT_PATH


def param_update(simulation, param, value):
    return simulation.set_parameter(param, value)


setA = partial(param_update, param="a")
setB = partial(param_update, param="b")
setC = partial(param_update, param="c")
setD = partial(param_update, param="d")


class TestMultipleBuilders(ITestWithPersistence):

    def setUp(self):
        super().setUp()
        self.base_path = os.path.abspath(os.path.join(INPUT_PATH, "builder"))
        self.arm_builder = ArmExperimentBuilder()
        self.yaml_builder = YamlExperimentBuilder()
        self.csv_builder = CsvExperimentBuilder()

    def tearDown(self):
        super().tearDown()

    def test_simple_builders(self):
        # create YamlExperimentBuilder
        file_path = os.path.join(self.base_path, 'sweeps.yaml')
        func_map = {'a': setA, 'b': setB, 'c': setC, 'd': setD}
        self.yaml_builder.add_sweeps_from_file(file_path, func_map)

        # create CsvExperimentBuilder
        file_path = os.path.join(self.base_path, 'sweeps.csv')
        func_map = {'a': setA, 'b': setB, 'c': setC, 'd': setD}
        type_map = {'a': np.int, 'b': np.int, 'c': np.int, 'd': np.int}
        self.csv_builder.add_sweeps_from_file(file_path, func_map, type_map)

        # create ArmExperimentBuilder
        arm = SweepArm(type=ArmType.cross)
        arm.add_sweep_definition(setA, range(2))
        arm.add_sweep_definition(setB, [1, 2, 3])
        self.arm_builder.add_arm(arm)

        # add individual builders
        experiment = TestExperiment("test")
        experiment.add_builder(self.yaml_builder)
        experiment.add_builder(self.csv_builder)
        experiment.add_builder(self.arm_builder)

        simulations = list(experiment.batch_simulations(50))[0]

        # test if we have correct number of simulations
        self.assertEqual(len(simulations), 10 + 5 + 6)

    def test_duplicates(self):
        arm = SweepArm(type=ArmType.cross)
        arm.add_sweep_definition(setA, range(2))
        arm.add_sweep_definition(setB, [1, 2, 3])
        self.arm_builder.add_arm(arm)

        # add individual builders
        experiment = TestExperiment("test")
        experiment.add_builder(self.arm_builder)
        experiment.add_builder(self.arm_builder)

        # test if we have correct number of builders
        self.assertEqual(len(experiment.builders), 1)

    def test_builder_property(self):
        arm = SweepArm(type=ArmType.cross)
        arm.add_sweep_definition(setA, range(2))
        arm.add_sweep_definition(setB, [1, 2, 3])
        self.arm_builder.add_arm(arm)

        # add individual builders
        experiment = TestExperiment("test")
        experiment.builder = self.arm_builder
        experiment.builder = self.csv_builder
        experiment.builder = self.yaml_builder

        # test if we have correct number of builders
        self.assertEqual(len(experiment.builders), 1)

        # test only the last builder has been added
        self.assertTrue(isinstance(list(experiment.builders)[0], YamlExperimentBuilder))

    def test_validation(self):
        a = TestExperiment(name="test")
        self.assertSetEqual(a.pickle_ignore_fields, {'builders'})

        with self.assertRaises(Exception):
            a.builder = 1

        # test no builder has been added
        self.assertIsNone(a.builders)