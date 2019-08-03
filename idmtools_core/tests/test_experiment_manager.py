import os
import unittest

from idmtools.builders import ExperimentBuilder
from idmtools.managers import ExperimentManager
from idmtools.services.experiments import ExperimentPersistService
from idmtools.services.platforms import PlatformPersistService
from idmtools_models.python import PythonExperiment
from idmtools_test.utils.ITestWithPersistence import ITestWithPersistence
from idmtools_test.utils.TstExperiment import TstExperiment
from idmtools_test.utils.TestPlatform import TestPlatform
from idmtools_test import COMMON_INPUT_PATH


def set_parameter_no_tags(simulation, value):
    simulation.set_parameter("p", value)


class TestExperimentManager(ITestWithPersistence):

    def test_from_experiment(self):
        e = TstExperiment("My experiment")
        p = TestPlatform()

        em = ExperimentManager(experiment=e, platform=p)
        em.run()

        em2 = ExperimentManager.from_experiment_id(e.uid, p)

        # Ensure we get the same thing when calling from_experiment
        self.assertEqual(em.experiment.base_simulation, em2.experiment.base_simulation)
        self.assertListEqual(em.experiment.simulations, em2.experiment.simulations)
        self.assertEqual(em.experiment, em2.experiment)
        self.assertEqual(em.platform, em2.platform)

    def test_from_experiment_unknown(self):
        c = TestPlatform()
        experiment = PythonExperiment(name="test_from_experiment",
                                      model_path=os.path.join(COMMON_INPUT_PATH, "compsplatform", "working_model.py"))
        builder = ExperimentBuilder()
        builder.add_sweep_definition(lambda simulation, value: {"p": value}, range(0, 2))
        experiment.builder = builder

        em = ExperimentManager(experiment=experiment, platform=c)
        em.run()
        self.assertEqual(len(em.experiment.simulations), 2)

        # Delete the experiment and platform from the stores
        ExperimentPersistService.delete(em.experiment.uid)
        PlatformPersistService.delete(em.experiment.platform_id)

        em2 = ExperimentManager.from_experiment_id(em.experiment.uid, platform=c)
        self.assertEqual(len(em2.experiment.simulations), 2)
        self.assertIsInstance(em2.experiment, PythonExperiment)
        self.assertDictEqual(em2.experiment.tags, experiment.tags)
        self.assertEqual(em2.experiment.platform_id, c.uid)


if __name__ == '__main__':
    unittest.main()
