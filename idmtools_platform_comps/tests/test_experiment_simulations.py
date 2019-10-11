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
        exp = EMODExperiment.from_default('simulation_test', default=EMODSir, eradication_path=DEFAULT_ERADICATION_PATH)
        exp.tags = {"idmtools": "idmtools-automation", "string_tag": "test", "number_tag": 123}
        exp.base_simulation.load_files(demographics_paths=DEFAULT_DEMOGRAPHICS_JSON)
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
        sim2.load_files(config_path=DEFAULT_CONFIG_PATH, campaign_path=DEFAULT_CAMPAIGN_JSON,
                        demographics_paths=DEFAULT_DEMOGRAPHICS_JSON)
        exp.simulations.append(sim2)

        platform = Platform('COMPS2')
        em = ExperimentManager(platform=platform, experiment=exp)
        em.create_experiment()
        em.create_simulations()

        # Check simulations
        sims = em.experiment.simulations
        children = em.experiment.children()

        self.assertEqual(len(sims), 2)
        self.assertEqual(len(children), 2 + num_sims)

    def test_simulation_experiment(self):
        exp = EMODExperiment()
        sim = exp.simulation()

        with self.assertRaises(Exception) as context:
            print(sim.experiment)
        self.assertIn('Items require a platform object to resolve their parent_id to an object',
                      context.exception.args[0])


if __name__ == '__main__':
    unittest.main()
