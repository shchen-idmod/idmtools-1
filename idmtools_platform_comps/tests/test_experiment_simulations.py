import os
import unittest
from idmtools.core.platform_factory import Platform
from idmtools_test.utils.itest_with_persistence import ITestWithPersistence

from idmtools_model_emod import EMODSimulation
from idmtools_model_emod import EMODExperiment

from idmtools_model_emod.defaults import EMODSir
from idmtools_test import COMMON_INPUT_PATH
from idmtools.builders import ExperimentBuilder
from idmtools.managers import ExperimentManager

DEFAULT_ERADICATION_PATH = os.path.join(COMMON_INPUT_PATH, "emod", "Eradication.exe")
DEFAULT_CONFIG_PATH = os.path.join(COMMON_INPUT_PATH, "files", "config.json")
DEFAULT_CAMPAIGN_JSON = os.path.join(COMMON_INPUT_PATH, "files", "campaign.json")
DEFAULT_DEMOGRAPHICS_JSON = os.path.join(COMMON_INPUT_PATH, "files", "demographics.json")


def param_a_update(simulation, value):
    simulation.set_parameter("Run_Number", value)
    return {"Run_Number": value}


class TestExperimentSimulations(ITestWithPersistence):

    def setUp(self):
        super().setUp()
        self.case_name = os.path.basename(__file__) + "--" + self._testMethodName
        print(self.case_name)

    def tearDown(self):
        super().tearDown()

    def test_input_simulations(self):
        # Create an experiment
        exp = EMODExperiment.from_default(self.case_name, default=EMODSir, eradication_path=DEFAULT_ERADICATION_PATH)
        exp.tags = {"idmtools": "idmtools-automation", "string_tag": "test", "number_tag": 123}
        exp.demographics.add_demographics_from_file(DEFAULT_DEMOGRAPHICS_JSON)
        exp.base_simulation.set_parameter("Enable_Immunity", 0)

        # User builder to create simulations
        num_sims = 3
        builder = ExperimentBuilder()
        builder.add_sweep_definition(param_a_update, range(0, num_sims))
        exp.builder = builder

        # Manually add simulation
        sim = exp.simulation()
        exp.simulations.append(sim)

        # Manually add simulation
        sim2 = EMODSimulation()
        sim2.load_files(config_path=DEFAULT_CONFIG_PATH, campaign_path=DEFAULT_CAMPAIGN_JSON)
        sim2.experiment = exp
        exp.simulations.append(sim2)

        platform = Platform('COMPS2')
        em = ExperimentManager(platform=platform, experiment=exp)
        em.create_experiment()
        em.create_simulations()

        # Check simulations
        sims = em.experiment.simulations

        self.assertEqual(len(sims), num_sims + 2)

    def test_simulation_experiment(self):
        exp = EMODExperiment()
        sim = exp.simulation()

        self.assertEqual(sim.experiment, exp)

    def test_create_suite(self):
        from idmtools.entities.suite import Suite
        from COMPS.Data import Suite as CompsSuite
        from idmtools_platform_comps.suite_utils import create_platform_suite

        suite = Suite(name='Idm Suite')
        suite.update_tags({'name': 'test', 'fetch': 123})

        platform = Platform('COMPS2')
        comps_suite = create_platform_suite(platform, suite)
        self.assertTrue(isinstance(comps_suite, CompsSuite))

    def test_suite_experiment(self):
        from idmtools.entities.suite import Suite
        from COMPS.Data import Suite as CompsSuite
        from idmtools.core import ItemType

        # Create an idm experiment
        exp = EMODExperiment.from_default(self.case_name, default=EMODSir, eradication_path=DEFAULT_ERADICATION_PATH)
        exp.tags = {"idmtools": "idmtools-automation", "string_tag": "test", "number_tag": 123}
        exp.base_simulation.demographics.add_demographics_from_file(DEFAULT_DEMOGRAPHICS_JSON)
        exp.base_simulation.set_parameter("Enable_Immunity", 0)

        # User builder to create simulations
        num_sims = 3
        builder = ExperimentBuilder()
        builder.add_sweep_definition(param_a_update, range(0, num_sims))
        exp.builder = builder

        # Create a idm suite
        suite = Suite(name='Idm Suite')
        suite.update_tags({'name': 'test', 'fetch': 123})

        # Create a platform
        platform = Platform('COMPS2')

        # Create COMPS experiment and run
        em = ExperimentManager(platform=platform, experiment=exp, suite=suite)
        em.run()
        em.wait_till_done()

        # Keep suite id
        suite_uid = suite.uid

        # Test suite retrieval
        comps_suite = platform.get_platform_item(item_id=suite_uid, item_type=ItemType.SUITE)
        self.assertTrue(isinstance(comps_suite, CompsSuite))

        # Test retrieve experiment from suite
        exps = platform.get_children_for_platform_item(comps_suite)
        self.assertEqual(len(exps), 1)

        exp = exps[0]
        self.assertTrue(isinstance(exp, EMODExperiment))
        self.assertIsNotNone(exp.parent)

        # Test get parent from experiment
        comps_exp = platform.get_platform_item(item_id=exp.uid, item_type=ItemType.EXPERIMENT)
        parent = platform.get_parent_for_platform_item(comps_exp)
        self.assertTrue(isinstance(parent, Suite))
        self.assertEqual(parent.uid, suite_uid)

        # Test retrieve simulations from experiment
        sims = platform.get_children_for_platform_item(comps_exp)
        self.assertEqual(len(sims), 3)

        sim = sims[0]
        self.assertTrue(isinstance(sim, EMODSimulation))
        self.assertIsNotNone(sim.parent)


if __name__ == '__main__':
    unittest.main()
