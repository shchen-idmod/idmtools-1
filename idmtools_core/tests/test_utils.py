import unittest
from idmtools.core import ExperimentNotFound, UnknownItemException
from idmtools.core.platform_factory import Platform
from idmtools.services.experiments import ExperimentPersistService
from idmtools.utils.entities import retrieve_experiment
from idmtools_test.utils.itest_with_persistence import ITestWithPersistence
from idmtools_test.utils.tst_experiment import TstExperiment


class TestUtils(ITestWithPersistence):

    def test_retrieve_experiment(self):
        # Test missing
        with self.assertRaises(UnknownItemException):
            retrieve_experiment("Missing", Platform('Test'))

        # Test correct retrieval
        e = TstExperiment("test")
        ExperimentPersistService.save(e)

        e2 = retrieve_experiment(e.uid)
        self.assertEqual(e, e2)

        # test correct retrieval with platform
        e = TstExperiment("test2")
        p = Platform('Test')
        p.create_items(items=[e])

        e.platform_id = p.uid
        with self.assertRaises(ExperimentNotFound):
            e2 = retrieve_experiment(e.uid)
        e2 = retrieve_experiment(e.uid, p)
        self.assertEqual(e2.metadata, e.metadata)


if __name__ == '__main__':
    unittest.main()
