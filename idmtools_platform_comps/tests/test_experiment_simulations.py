import os
import unittest

import pytest
from COMPS.Data import Suite as CompsSuite, Experiment as CompsExperiment, Simulation as CompsSimulation

from idmtools.builders import SimulationBuilder
from idmtools.core import ItemType
from idmtools.core.platform_factory import Platform
from idmtools.entities import Suite
from idmtools_test import COMMON_INPUT_PATH
from idmtools_test.utils.itest_with_persistence import ITestWithPersistence

DEFAULT_ERADICATION_PATH = os.path.join(COMMON_INPUT_PATH, "emod", "Eradication.exe")
DEFAULT_CONFIG_PATH = os.path.join(COMMON_INPUT_PATH, "files", "config.json")
DEFAULT_CAMPAIGN_JSON = os.path.join(COMMON_INPUT_PATH, "files", "campaign.json")
DEFAULT_DEMOGRAPHICS_JSON = os.path.join(COMMON_INPUT_PATH, "files", "demographics.json")


def param_a_update(simulation, value):
    simulation.set_parameter("Run_Number", value)
    return {"Run_Number": value}


@pytest.mark.skip
class TestExperimentSimulations(ITestWithPersistence):

    def get_sir_experiment(self, case_name):
        exp = EMODExperiment.from_default(case_name, default=EMODSir(), eradication_path=DEFAULT_ERADICATION_PATH)  # noqa: F821
        exp.tags = {"idmtools": "idmtools-automation", "string_tag": "test", "number_tag": 123}
        exp.base_simulation.demographics.add_demographics_from_file(DEFAULT_DEMOGRAPHICS_JSON)
        exp.base_simulation.set_parameter("Enable_Immunity", 0)
        # User builder to create simulations
        num_sims = 3
        builder = SimulationBuilder()
        builder.add_sweep_definition(param_a_update, range(0, num_sims))
        exp.builder = builder
        return exp

    def setUp(self):
        super().setUp()
        self.case_name = os.path.basename(__file__) + "--" + self._testMethodName
        print(self.case_name)

    def tearDown(self):
        super().tearDown()

    @pytest.mark.emod
    @pytest.mark.comps
    def test_input_simulations(self):
        # Create an experiment
        exp = EMODExperiment.from_default(self.case_name, default=EMODSir(), eradication_path=DEFAULT_ERADICATION_PATH)  # noqa: F821
        exp.tags = {"idmtools": "idmtools-automation", "string_tag": "test", "number_tag": 123}
        exp.demographics.add_demographics_from_file(DEFAULT_DEMOGRAPHICS_JSON)
        exp.base_simulation.set_parameter("Enable_Immunity", 0)

        # User builder to create simulations
        num_sims = 3
        builder = SimulationBuilder()
        builder.add_sweep_definition(param_a_update, range(0, num_sims))
        exp.builder = builder

        # Manually add simulation
        sim = exp.simulation()
        exp.simulations.append(sim)

        # Manually add simulation
        sim2 = EMODSimulation()  # noqa: F821
        sim2.load_files(config_path=DEFAULT_CONFIG_PATH, campaign_path=DEFAULT_CAMPAIGN_JSON)
        sim2.experiment = exp
        exp.simulations.append(sim2)

        platform = Platform('COMPS2')
        em = ExperimentManager(platform=platform, experiment=exp)  # noqa: F821
        em.create_experiment()
        em.create_simulations()

        # Check simulations
        sims = em.experiment.simulations

        self.assertEqual(len(sims), num_sims + 2)

    @pytest.mark.comps
    @pytest.mark.suite
    def test_create_suite(self):
        from idmtools.entities.suite import Suite
        from COMPS.Data import Suite as CompsSuite
        from idmtools.core import ItemType

        suite = Suite(name='Idm Suite')
        suite.update_tags({'name': 'test', 'fetch': 123})

        platform = Platform('COMPS2')
        ids = platform.create_items([suite])

        suite_uid = ids[0]
        comps_suite = platform.get_item(item_id=suite_uid, item_type=ItemType.SUITE, raw=True)
        self.assertTrue(isinstance(comps_suite, CompsSuite))

    def run_experiment_and_test_suite(self, em, platform, suite):
        # Run experiment
        em.run()
        em.wait_till_done()
        # Keep suite id
        suite_uid = suite.uid
        # ################## Test raw
        # Test suite retrieval
        comps_suite = platform.get_item(item_id=suite_uid, item_type=ItemType.SUITE, raw=True)
        self.assertTrue(isinstance(comps_suite, CompsSuite))
        # Test retrieve experiment from suite
        exps = platform._get_children_for_platform_item(comps_suite)
        self.assertEqual(len(exps), 1)
        exp = exps[0]
        self.assertTrue(isinstance(exp, CompsExperiment))
        self.assertIsNotNone(exp.suite_id)
        # Test get parent from experiment
        comps_exp = platform.get_item(item_id=exp.id, item_type=ItemType.EXPERIMENT, raw=True)
        parent = platform._get_parent_for_platform_item(comps_exp)
        self.assertTrue(isinstance(parent, CompsSuite))
        self.assertEqual(parent.id, suite_uid)
        # Test retrieve simulations from experiment

        sims = platform._get_children_for_platform_item(comps_exp)
        self.assertEqual(len(sims), 3)
        sim = sims[0]
        self.assertTrue(isinstance(sim, CompsSimulation))
        self.assertIsNotNone(sim.experiment_id)

        # ### Test idmtools objects
        # Test suite retrieval
        comps_suite = platform.get_item(item_id=suite_uid, item_type=ItemType.SUITE)
        self.assertTrue(isinstance(comps_suite, Suite))
        # Test retrieve experiment from suite
        exps = platform.get_children_by_object(comps_suite)
        self.assertEqual(len(exps), 1)
        exp = exps[0]
        self.assertTrue(isinstance(exp, EMODExperiment))  # noqa: F821
        self.assertIsNotNone(exp.parent)
        # Test get parent from experiment
        comps_exp = platform.get_item(item_id=exp.uid, item_type=ItemType.EXPERIMENT)
        parent = platform.get_parent_by_object(comps_exp)
        self.assertTrue(isinstance(parent, Suite))
        self.assertEqual(parent.uid, suite_uid)
        # Test retrieve simulations from experiment

        sims = platform.get_children_by_object(comps_exp)
        self.assertEqual(len(sims), 3)
        sim = sims[0]
        self.assertTrue(isinstance(sim, EMODSimulation))  # noqa: F821
        self.assertIsNotNone(sim.parent)

    @pytest.mark.comps
    @pytest.mark.emod
    @pytest.mark.suite
    @pytest.mark.long
    def test_link_experiment_suite(self):
        from idmtools.entities.suite import Suite

        # Create an idm experiment
        exp = self.get_sir_experiment(self.case_name)

        # Create a platform
        platform = Platform('COMPS2')

        # Create COMPS experiment and run
        em = ExperimentManager(platform=platform, experiment=exp)  # noqa: F821

        # Create a idm suite
        suite = Suite(name='Idm Suite 1')
        suite.update_tags({'name': 'test', 'fetch': 123})

        # Create platform suite
        platform.create_items([suite])

        # Add experiment to the suite
        suite.add_experiment(em.experiment)

        self.run_experiment_and_test_suite(em, platform, suite)

    @pytest.mark.comps
    @pytest.mark.emod
    @pytest.mark.suite
    @pytest.mark.long
    def test_suite_experiment(self):
        from idmtools.entities.suite import Suite

        # Create an idm experiment
        exp = self.get_sir_experiment(self.case_name)

        # Create a idm suite
        suite = Suite(name='Idm Suite')
        suite.update_tags({'name': 'test', 'fetch': 123})

        # Create a platform
        platform = Platform('COMPS2')

        # Create COMPS experiment and run
        em = ExperimentManager(platform=platform, experiment=exp, suite=suite)  # noqa: F821
        self.run_experiment_and_test_suite(em, platform, suite)


if __name__ == '__main__':
    unittest.main()
