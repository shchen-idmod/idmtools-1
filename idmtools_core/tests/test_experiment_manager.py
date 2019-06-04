import unittest

from idmtools.entities import IExperiment
from idmtools.managers import ExperimentManager
from idmtools.platforms import LocalPlatform
from idmtools.services.experiments import ExperimentPersistService
from idmtools.services.platforms import PlatformPersistService
from tests.ITestWithPersistence import ITestWithPersistence


class TestExperimentManager(ITestWithPersistence):

    def test_from_experiment(self):
        e = IExperiment("My experiment")
        p = LocalPlatform()

        em = ExperimentManager(experiment=e, platform=p)
        em.create_experiment()
        em.create_simulations()

        em2 = ExperimentManager.from_experiment_id(e.uid)

        # Ensure we get the same thing when calling from_experiment
        self.assertListEqual(em.experiment.simulations, em2.experiment.simulations)
        self.assertEqual(em.experiment, em2.experiment)
        self.assertEqual(em.platform, em2.platform)

        # Ensure we have the status persisted too
        em.start_experiment()
        em.wait_till_done()
        e = ExperimentPersistService.retrieve(e.uid)
        self.assertEqual(e, em.experiment)


if __name__ == '__main__':
    unittest.main()
