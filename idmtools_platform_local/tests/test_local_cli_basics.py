# flake8: noqa E402
import re
import time
import unittest.mock
import os
import pytest
from click._compat import strip_ansi
from sqlalchemy.exc import OperationalError

from idmtools.core.platform_factory import Platform
from idmtools_test.utils.decorators import restart_local_platform

api_host = os.getenv('API_HOST', 'localhost')
os.environ['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2://idmtools:idmtools@{api_host}/idmtools'
from idmtools_platform_local.status import Status
from idmtools_platform_local.internals.workers.utils import create_or_update_status
from idmtools_test.utils.cli import get_subcommands_from_help_result, run_command


@pytest.mark.docker
@pytest.mark.local_platform_cli
class TestLocalCLIBasic(unittest.TestCase):

    @classmethod
    @restart_local_platform(silent=True, stop_after=False)
    def setUpClass(cls):
        platform = Platform('Local')
        retries = 0
        while retries < 10:
            try:
                cls.create_test_data()
                break
            except (OperationalError, ConnectionError):
                time.sleep(0.5)
                retries += 1

    @classmethod
    @restart_local_platform(silent=True, stop_before=False)
    def tearDownClass(cls) -> None:
        pass

    @staticmethod
    def create_test_data():
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
                                status=Status.done,
                                extra_details=dict(simulation_type='Python'))
        create_or_update_status('FFFFF', '/data/FFFFF', dict(i='j', k='l'), parent_uuid='DDDDD',
                                status=Status.done,
                                extra_details=dict(simulation_type='Python'))

    @staticmethod
    def run_command(*args, start_command=None, base_command=None):
        if start_command is None:
            start_command = []
        if base_command:
            start_command.append(base_command)
        return run_command(*args, start_command=start_command)

    def test_load(self):
        result = self.run_command('experiment', '--platform', 'Local', '--help', base_command='')
        lines = get_subcommands_from_help_result(result)
        # ensure our command is in the options
        self.assertIn('status', lines)

    def test_status(self):
        result = self.run_command('experiment', '--platform', 'Local', 'status', base_command='')
        print(result)

    @pytest.mark.long
    def test_docker(self):
        """
        Filtering depends on a few postgres filtering method so we have to
        setup a connection to postgres and then test querying
        """

        with self.subTest("test_experiments_status"):
            # this is ugly but something odd is going on with db on windows
            # it could be artifacts in tests but it appears db takes a moment to respond with experiments
            time.sleep(10 if os.name == "nt" else 1)

            result = self.run_command('experiment', '--platform', 'Local', 'status', base_command='')
            self.assertEqual(result.exit_code, 0, f'{result.exit_code} - {result.output}')
            output = re.sub(r'[\+\-]+', '', result.output).split("\n")
            output = [o for o in output if o and len(o) > 3 and 'experiment_id' not in o]
            self.assertEqual(len(output), 3)
            rows = list(map(lambda x: list(map(str.strip, x)), [s.split('|') for s in output]))
            self.assertEqual(rows[0][1], "DDDDD")
            self.assertEqual(rows[1][1], "BBBBB")
            self.assertEqual(rows[2][1], "AAAAA")

        with self.subTest("test_simulation_status"):
            result = self.run_command('simulation', '--platform', 'Local', 'status', base_command='')
            self.assertEqual(result.exit_code, 0, f'{result.exit_code} - {result.output}')
            output = re.sub(r'[\+\-]+', '', strip_ansi(result.output)).split("\n")
            output = [o for o in output if o and len(o) > 3 and 'simulation_uid' not in o]
            self.assertEqual(len(output), 3)
            rows = list(map(lambda x: list(map(str.strip, x)), [s.split('|') for s in output]))
            self.assertEqual(rows[0][1], "FFFFF")
            self.assertEqual(rows[0][2], "DDDDD")
            self.assertEqual(rows[0][3], "done")
            self.assertEqual(rows[1][1], "EEEEE")
            self.assertEqual(rows[1][2], "DDDDD")
            self.assertEqual(rows[1][3], "done")
            self.assertEqual(rows[2][1], "CCCCC")
            self.assertEqual(rows[2][2], "BBBBB")
            self.assertEqual(rows[2][3], "created")