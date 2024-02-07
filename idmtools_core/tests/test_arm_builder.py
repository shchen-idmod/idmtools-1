import allure
import itertools
from functools import partial

import pytest
from idmtools.builders.arm_simulation_builder import ArmSimulationBuilder, SweepArm, ArmType
from idmtools.entities.templated_simulation import TemplatedSimulations
from idmtools_models.json_configured_task import JSONConfiguredTask
from idmtools_test.utils.itest_with_persistence import ITestWithPersistence
from idmtools_test.utils.test_task import TestTask

setA = partial(JSONConfiguredTask.set_parameter_sweep_callback, param="a")
setB = partial(JSONConfiguredTask.set_parameter_sweep_callback, param="b")


def update_parameter_callback(simulation, a, b, c):
    simulation.task.command.add_argument(a)
    simulation.task.command.add_argument(b)
    simulation.task.command.add_argument(c)
    return {"a": a, "b": b, "c": c}


@pytest.mark.smoke
@allure.story("Sweeps")
@allure.suite("idmtools_core")
class TestArmBuilder(ITestWithPersistence):

    def setUp(self):
        super().setUp()
        self.builder = ArmSimulationBuilder()

    def tearDown(self):
        super().tearDown()

    def test_simple_arm_cross(self):
        self.create_simple_arm()

        expected_values = list(itertools.product(range(5), [1, 2, 3]))
        templated_sim = self.get_templated_sim_builder()

        # convert template to a fully realized list
        simulations = list(templated_sim)

        # Test if we have correct number of simulations
        self.assertEqual(len(simulations), 15)

        # Verify simulations individually
        for i, simulation in enumerate(simulations):
            expected_dict = {"a": expected_values[i][0], "b": expected_values[i][1]}
            self.assertEqual(simulation.task.parameters, expected_dict)

    def get_templated_sim_builder(self):
        templated_sim = TemplatedSimulations(base_task=TestTask())
        templated_sim.builder = self.builder
        return templated_sim

    def create_simple_arm(self):
        arm = SweepArm(type=ArmType.cross)
        arm.add_sweep_definition(setA, range(5))
        arm.add_sweep_definition(setB, [1, 2, 3])
        self.builder.add_arm(arm)

    def test_reverse_order(self):
        self.create_simple_arm()

        templated_sim = self.get_templated_sim_builder()

        # convert template to a fully realized list
        simulations_cfgs = list([s.task.parameters for s in templated_sim])

        builder2 = ArmSimulationBuilder()

        arm = SweepArm(type=ArmType.cross)
        a = [1, 2, 3]
        b = range(5)
        arm.add_sweep_definition(setB, a)
        arm.add_sweep_definition(setA, b)
        builder2.add_arm(arm)
        self.assertEqual(builder2.count, a.__len__() * b.__len__())

        # convert template to a fully realized list
        templated_sim2 = TemplatedSimulations(base_task=TestTask())
        templated_sim2.builder = builder2

        simulations2_cfgs = list([s.task.parameters for s in templated_sim2])

        for cfg in simulations_cfgs:
            self.assertIn(dict(b=cfg['b'], a=cfg['a']), simulations2_cfgs)

    def test_simple_arm_pair_uneven_pairs(self):
        with self.assertRaises(ValueError) as ex:
            arm = SweepArm(type=ArmType.pair)
            a = range(5)
            b = [1, 2, 3]
            arm.add_sweep_definition(setA, a)
            arm.add_sweep_definition(setB, b)  # Adding different length of list, expect throw exception
            self.builder.add_arm(arm)
        self.assertEqual(ex.exception.args[0],
                         f"For pair case, all function inputs must have the save size/length: {b.__len__()} != {a.__len__()}")

    def test_simple_arm_pair(self):
        arm = SweepArm(type=ArmType.pair)
        a = range(5)
        # Add same length pair
        b = [1, 2, 3, 4, 5]
        arm.add_sweep_definition(setA, a)
        arm.add_sweep_definition(setB, b)
        self.builder.add_arm(arm)
        self.assertEqual(self.builder.count, 5)

        expected_values = list(zip(a, b))

        templated_sim = self.get_templated_sim_builder()
        simulations = list(templated_sim)
        # Test if we have correct number of simulations
        self.assertEqual(len(simulations), 5)

        # Verify simulations individually
        for i, simulation in enumerate(simulations):
            expected_dict = {"a": expected_values[i][0], "b": expected_values[i][1]}
            self.assertEqual(simulation.task.parameters, expected_dict)

    def test_add_multiple_parameter_sweep_definition(self):
        a = [True, False]
        b = [1, 2, 3, 4, 5]
        c = "test"
        with self.assertRaises(ValueError) as ex:
            self.builder.add_multiple_parameter_sweep_definition(update_parameter_callback, a, b, c)
        self.assertEqual(ex.exception.args[0], "Please use SweepArm instead, or use SimulationBuilder directly!")

    def test_single_item_arm_builder(self):
        arm = SweepArm()
        a = 10  # test only one item not list
        b = [1, 2, 3, 4, 5]
        arm.add_sweep_definition(setA, a)
        arm.add_sweep_definition(setB, b)
        self.builder.add_arm(arm)
        self.assertEqual(self.builder.count, 5)

    def test_dict_arm_builder(self):
        arm = SweepArm()
        a = [{"first": 10}, {"second": 20}]
        b = [1, 2, 3]
        arm.add_sweep_definition(setA, a)
        arm.add_sweep_definition(setB, b)
        self.builder.add_arm(arm)
        self.assertEqual(self.builder.count, 6)
        templated_sim = self.get_templated_sim_builder()
        simulations = list(templated_sim)
        # Test if we have correct number of simulations
        self.assertEqual(len(simulations), 6)
        expected_values = [{'a': {'first': 10}, 'b': 1},
                           {'a': {'first': 10}, 'b': 2},
                           {'a': {'first': 10}, 'b': 3},
                           {'a': {'second': 20}, 'b': 1},
                           {'a': {'second': 20}, 'b': 2},
                           {'a': {'second': 20}, 'b': 3}
                           ]
        # Verify simulations individually
        for i, simulation in enumerate(simulations):
            self.assertEqual(simulation.task.parameters, expected_values[i])

    def test_single_item_arm_builder(self):
        arm = SweepArm()
        a = 10  # test only one item not list
        b = [1, 2, 3, 4, 5]
        arm.add_sweep_definition(setA, a)
        arm.add_sweep_definition(setB, b)
        self.builder.add_arm(arm)
        self.assertEqual(self.builder.count, 5)

    def test_single_dict_arm_builder(self):
        arm = SweepArm()
        a = {"first": 10}  # test only one dict
        b = [1, 2, 3]
        arm.add_sweep_definition(setA, a)
        arm.add_sweep_definition(setB, b)
        self.builder.add_arm(arm)
        self.assertEqual(self.builder.count, 3)
        templated_sim = self.get_templated_sim_builder()
        simulations = list(templated_sim)
        # Test if we have correct number of simulations
        self.assertEqual(len(simulations), 3)
        expected_values = [{'a': {'first': 10}, 'b': 1},
                           {'a': {'first': 10}, 'b': 2},
                           {'a': {'first': 10}, 'b': 3}
                           ]
        # Verify simulations individually
        for i, simulation in enumerate(simulations):
            self.assertEqual(simulation.task.parameters, expected_values[i])

    def test_single_string_arm_builder(self):
        arm = SweepArm()
        a = "test"  # test only 1 string
        b = [1, 2, 3]
        arm.add_sweep_definition(setA, a)
        arm.add_sweep_definition(setB, b)
        self.builder.add_arm(arm)
        self.assertEqual(self.builder.count, 3)
        templated_sim = self.get_templated_sim_builder()
        simulations = list(templated_sim)
        # Test if we have correct number of simulations
        self.assertEqual(len(simulations), 3)
        expected_values = [{'a': 'test', 'b': 1},
                           {'a': 'test', 'b': 2},
                           {'a': 'test', 'b': 3}
                           ]
        # Verify simulations individually
        for i, simulation in enumerate(simulations):
            self.assertEqual(simulation.task.parameters, expected_values[i])

    def test_single_list_arm_builder(self):
        arm = SweepArm()
        a = [10]  # test only one item in list
        b = [1, 2, 3]
        arm.add_sweep_definition(setA, a)
        arm.add_sweep_definition(setB, b)
        self.builder.add_arm(arm)
        self.assertEqual(self.builder.count, 3)
        templated_sim = self.get_templated_sim_builder()
        simulations = list(templated_sim)
        # Test if we have correct number of simulations
        self.assertEqual(len(simulations), 3)
        expected_values = [{'a': 10, 'b': 1},
                           {'a': 10, 'b': 2},
                           {'a': 10, 'b': 3}
                           ]
        # Verify simulations individually
        for i, simulation in enumerate(simulations):
            self.assertEqual(simulation.task.parameters, expected_values[i])

    def test_tuple_arm_builder(self):
        arm = SweepArm()
        a = (4, 5, 6)  # test tuple
        b = [1, 2, 3]
        arm.add_sweep_definition(setA, a)
        arm.add_sweep_definition(setB, b)
        self.builder.add_arm(arm)
        self.assertEqual(self.builder.count, 9)
        templated_sim = self.get_templated_sim_builder()
        simulations = list(templated_sim)
        # Test if we have correct number of simulations
        self.assertEqual(len(simulations), 9)
        expected_values = [{'a': 4, 'b': 1},
                           {'a': 4, 'b': 2},
                           {'a': 4, 'b': 3},
                           {'a': 5, 'b': 1},
                           {'a': 5, 'b': 2},
                           {'a': 5, 'b': 3},
                           {'a': 6, 'b': 1},
                           {'a': 6, 'b': 2},
                           {'a': 6, 'b': 3}
                           ]
        # Verify simulations individually
        for i, simulation in enumerate(simulations):
            self.assertEqual(simulation.task.parameters, expected_values[i])
