# flake8: noqa E402
import os
import time
import unittest.mock
from importlib import reload
import docker
import pytest
from operator import itemgetter

from sqlalchemy.exc import OperationalError

from idmtools_platform_local.internals.workers.database import reset_db

api_host = os.getenv('API_HOST', 'localhost')
os.environ['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://idmtools:idmtools@{api_host}/idmtools'
from idmtools_platform_local.internals.workers.utils import create_or_update_status
from idmtools_test.utils.confg_local_runner_test import config_local_test, patch_broker, reset_local_broker
from idmtools_platform_local.internals.infrastructure.service_manager import DockerServiceManager


@pytest.mark.docker
@pytest.mark.local_platform_internals
class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        sm = DockerServiceManager(docker.from_env())
        sm.cleanup(delete_data=True,tear_down_brokers=True)
        sm.get_network()
        sm.get('postgres')
        sm.wait_on_ports_to_open(['postgres_port'])
        retries = 0
        while retries < 10:
            try:
                cls.create_test_data()
                break
            except (OperationalError, ConnectionError):
                time.sleep(0.5)
                retries += 1

    @patch_broker
    def setUp(self, mock_broker):
        local_path = config_local_test()  # noqa: F841
        config_local_test()

        from idmtools_platform_local.internals.ui.app import application
        self.app = application.test_client()

    @classmethod
    def tearDownClass(cls) -> None:
        import idmtools_platform_local.internals.workers.brokers
        reload(idmtools_platform_local.internals.workers.brokers)
        reset_db()
        reset_local_broker()

    @staticmethod
    def create_test_data():
        from idmtools_platform_local.internals.workers.database import get_session
        from idmtools_platform_local.internals.data.job_status import JobStatus
        # delete any previous data

        get_session().query(JobStatus).delete()
        # this experiment has no children
        create_or_update_status('AAAAA', '/data/AAAAA', dict(a='b', c='d'),
                                extra_details=dict(simulation_type='Python'))
        # Experiment
        create_or_update_status('BBBBB', '/data/BBBBB', dict(e='f', g='h'),
                                extra_details=dict(simulation_type='Python'))
        # Simulation
        create_or_update_status('CCCCC', '/data/CCCCC', dict(i='j', k='l'), parent_uuid='BBBBB',
                                extra_details=dict(simulation_type='Python'))
        # Experiment
        create_or_update_status('DDDDD', '/data/DDDD', dict(e='f', c='d'),
                                extra_details=dict(simulation_type='Python'))

        # Simulation
        create_or_update_status('EEEEE', '/data/EEEEE', dict(i='j', k='l'), parent_uuid='DDDDD',
                                extra_details=dict(simulation_type='Python'))
        create_or_update_status('FFFFF', '/data/FFFFF', dict(i='j', k='l'), parent_uuid='DDDDD',
                                extra_details=dict(simulation_type='Python'))

    def test_fetch_experiments(self):
        # ensure we have some phony data

        result = self.app.get('/api/experiments')
        self.assertEqual(200, result.status_code)

        data = result.json
        self.assertIsInstance(data, list)
        # ensure we know the order for testing
        data = sorted(data, key=itemgetter('experiment_id'))

        self.assertEqual(data[0]['experiment_id'], 'AAAAA')
        # make sure our simulation is not in our experiment list
        self.assertNotIn('CCCCC', map(itemgetter('experiment_id'), data))
        self.assertEqual(data[1]['experiment_id'], 'BBBBB')
        self.assertEqual(len(data[1]['progress']), 1)
        self.assertIn('created', data[1]['progress'])
        self.assertEqual(data[1]['progress']['created'], 1)

    def test_fetch_one_experiment_works(self):
        result = self.app.get('/api/experiments/AAAAA')
        self.assertEqual(200, result.status_code)

        data = result.json
        self.assertIsInstance(data, dict)
        self.assertEqual(data['experiment_id'], 'AAAAA')
        self.assertDictEqual(data['tags'], dict(a='b', c='d'))
        self.assertEqual(data['data_path'], '/data/AAAAA')

    def test_fetch_simulations(self):
        # ensure we have some phony data

        result = self.app.get('/api/simulations')
        self.assertEqual(200, result.status_code)

        data = result.json
        self.assertIsInstance(data, list)
        # ensure we know the order for testing
        data = sorted(data, key=itemgetter('simulation_uid'))

        self.assertEqual(data[0]['simulation_uid'], 'CCCCC')
        # make sure our simulation is not in our experiment list
        self.assertNotIn('AAAAA', map(itemgetter('simulation_uid'), data))
        self.assertEqual(data[0]['experiment_id'], 'BBBBB')

        result = self.app.get('/api/simulations', query_string=dict(experiment_id='DDDDD'))
        self.assertEqual(200, result.status_code)

        data = result.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    def test_fetch_one_simulation_works(self):
        result = self.app.get('/api/simulations/CCCCC')
        self.assertEqual(200, result.status_code)

        data = result.json
        self.assertIsInstance(data, dict)
        self.assertEqual(data['simulation_uid'], 'CCCCC')
        self.assertEqual(data['experiment_id'], 'BBBBB')
        self.assertDictEqual(data['tags'], dict(i='j', k='l'))
        self.assertEqual(data['data_path'], '/data/CCCCC')

    def test_experiment_filtering(self):
        result = self.app.get('/api/experiments', query_string=dict(tags='a,b'))
        self.assertEqual(200, result.status_code)
        data = result.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(result.json), 1)

        result = self.app.get('/api/experiments', query_string=dict(tags='a,c'))
        self.assertEqual(200, result.status_code)
        data = result.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(result.json), 0)
