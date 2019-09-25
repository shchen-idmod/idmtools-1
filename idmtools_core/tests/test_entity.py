import copy
import pickle
import unittest
from dataclasses import dataclass, field
from idmtools.builders import ExperimentBuilder
from idmtools.core.interfaces.ientity import IEntity
from idmtools.entities.suite import Suite
from idmtools_test.utils.itest_with_persistence import ITestWithPersistence
from idmtools_test.utils.tst_experiment import TstExperiment


@dataclass
class EntityWithIgnoreField(IEntity):
    ignore: int = field(default=3, compare=False, metadata={"pickle_ignore": True})
    ignore_with_restore: int = field(default=1, compare=False, metadata={"pickle_ignore": True})
    not_ignored: int = field(default=4, metadata={"md": True})

    def post_setstate(self):
        self.ignore_with_restore = 5


def _custom_post_setstate(o):
    o.ignore = 5


class TestEntity(ITestWithPersistence):

    def test_hashing(self):
        a = IEntity()
        a.tags = {"a": 1}

        c = IEntity()
        c.tags = {"a": 2}
        self.assertNotEqual(a, c)

        b = IEntity()
        b.tags = {"a": 1}

        # Those 2 entities are the same because same elements
        self.assertEqual(a, b)

        # a and c should be identical after deepcopy
        c = copy.deepcopy(a)
        self.assertEqual(a, c)

        # a and b should be identical after pickling
        b = pickle.loads(pickle.dumps(a))
        self.assertEqual(a, b)

    def test_pickle_ignore(self):
        from idmtools.assets import AssetCollection
        from idmtools.core import EntityContainer

        a = TstExperiment(name="test")
        self.assertSetEqual(a.pickle_ignore_fields, {'assets', 'simulations', 'builders'})
        a.builder = ExperimentBuilder()

        b = pickle.loads(pickle.dumps(a))
        self.assertSetEqual(b.builders, set())
        self.assertEqual(b.assets, AssetCollection())
        self.assertEqual(b.simulations, EntityContainer())

        s = Suite(name="test")
        self.assertSetEqual(s.pickle_ignore_fields, {"experiments"})
        b = pickle.loads(pickle.dumps(s))
        self.assertEqual(b.experiments, [])

        a = EntityWithIgnoreField(ignore=10, ignore_with_restore=5)
        self.assertEqual(a.ignore, 10)
        self.assertEqual(a.ignore_with_restore, 5)
        self.assertEqual(a.not_ignored, 4)

        b = pickle.loads(pickle.dumps(a))
        self.assertNotEqual(b.ignore, a.ignore)
        self.assertEqual(b.not_ignored, a.not_ignored)
        self.assertEqual(b.ignore_with_restore, 5)

        # Test that object remains equal even with different parameters if those are not part of compare
        a = EntityWithIgnoreField()
        b = EntityWithIgnoreField()
        a.ignore = "A"
        b.ignore_with_restore = 10
        self.assertEqual(a, b)
        a.not_ignored = 100
        self.assertNotEqual(a, b)

        # Test that we do not change the object while doing equality tests
        self.assertEqual(b.ignore_with_restore, 10)

    def test_suite(self):
        s = Suite(name="test")
        self.assertEqual(s.name, "test")

        s.experiments.append(TstExperiment("t1"))
        s.experiments.append(TstExperiment("t2"))
        self.assertEqual(len(s.experiments), 2)


if __name__ == '__main__':
    unittest.main()
