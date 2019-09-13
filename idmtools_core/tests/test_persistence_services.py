import unittest
from idmtools.core.PlatformFactory import Platform
from idmtools.services.experiments import ExperimentPersistService
from idmtools.services.platforms import PlatformPersistService
from idmtools_test.utils.ITestWithPersistence import ITestWithPersistence
from idmtools_test.utils.TstExperiment import TstExperiment


class TestPersistenceServices(ITestWithPersistence):

    def test_persist_retrieve_platform(self):
        p = Platform('Test')
        PlatformPersistService.save(p)
        p2 = PlatformPersistService.retrieve(p.uid)
        self.assertEqual(p, p2)

    def test_persist_retrieve_experiment(self):
        e = TstExperiment("test")
        e.simulation()
        ExperimentPersistService.save(e)
        e2 = ExperimentPersistService.retrieve(e.uid)
        self.assertEqual(e, e2)
        # Simulations should not be persisted
        self.assertEqual(e2.simulations, [])

        e3 = ExperimentPersistService.retrieve("Missing")
        self.assertIsNone(e3)


if __name__ == '__main__':
    unittest.main()
