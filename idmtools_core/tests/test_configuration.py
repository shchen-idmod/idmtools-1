import io
import tempfile
import unittest.mock
import os
import pytest
from idmtools.config import IdmConfigParser
from idmtools.core.PlatformFactory import Platform
from idmtools_platform_comps.COMPSPlatform import COMPSPlatform
from idmtools_test import COMMON_INPUT_PATH
from idmtools_test.utils.ITestWithPersistence import ITestWithPersistence


class TestConfig(ITestWithPersistence):

    def setUp(self):
        super().setUp()
        IdmConfigParser.clear_instance()

    def tearDown(self):
        super().tearDown()

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_reports_no_file_found(self, mock_stdout):
        fdir = tempfile.mkdtemp()
        IdmConfigParser(fdir)
        self.assertIn("WARNING: File 'idmtools.ini' Not Found!", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_load_not_found(self, mock_stdout):
        fdir = tempfile.mkdtemp()
        IdmConfigParser._load_config_file(fdir, 'aaaaa')
        self.assertIn("WARNING: File 'aaaaa' Not Found!", mock_stdout.getvalue())

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_section_not_found(self, mock_stdout):
        IdmConfigParser().get_section('NotReallyASection')
        self.assertIn("WARNING: Section 'NotReallyASection' Not Found!", mock_stdout.getvalue())

    @pytest.mark.comps
    @unittest.mock.patch('idmtools_platform_comps.COMPSPlatform.COMPSPlatform._login', side_effect=lambda: True)
    def test_simple_comps_platform_use_config(self, mock_login):
        platform = Platform("COMPS")
        self.assertEqual(platform.endpoint, 'https://comps2.idmod.org')
        self.assertEqual(platform.environment, 'Bayesian')
        self.assertEqual(mock_login.call_count, 1)

    @pytest.mark.comps
    @unittest.mock.patch('idmtools_platform_comps.COMPSPlatform.COMPSPlatform._login', side_effect=lambda: True)
    def test_simple_comps_platform_use_code(self, mock_login):
        platform = Platform("COMPS", endpoint='https://abc', environment='Bayesian')
        self.assertEqual(platform.endpoint, 'https://abc')
        self.assertEqual(platform.environment, 'Bayesian')
        self.assertEqual(mock_login.call_count, 1)

    def test_idmtools_ini(self):
        config_file = IdmConfigParser.get_config_path()
        self.assertEqual(os.path.basename(config_file), 'idmtools.ini')

        max_threads = IdmConfigParser.get_option("COMMON", 'max_threads')
        self.assertEqual(int(max_threads), 16)

        idm = IdmConfigParser()
        max_threads = idm.get_option("COMMON", 'max_threads')
        self.assertEqual(int(max_threads), 16)

    @pytest.mark.comps
    @unittest.mock.patch('idmtools_platform_comps.COMPSPlatform.COMPSPlatform._login', side_effect=lambda: True)
    def test_idmtools_path(self, login_mock):
        IdmConfigParser(os.path.join(COMMON_INPUT_PATH, "configuration"), "idmtools_test.ini")
        platform = COMPSPlatform()
        self.assertEqual(platform.num_retires, int(IdmConfigParser.get_option('COMPS', 'num_retires')))

        file_path = os.path.join(COMMON_INPUT_PATH, "configuration", "idmtools_test.ini")
        self.assertEqual(IdmConfigParser.get_config_path(), os.path.abspath(file_path))

    def test_IdmConfigParser_singleton(self):
        p1 = IdmConfigParser()
        p2 = IdmConfigParser()

        self.assertEqual(p1, p2)
        self.assertEqual(id(p1), id(p2))

    def test_no_idmtools(self):
        IdmConfigParser(file_name="idmtools_NotExist.ini")
        IdmConfigParser.view_config_file()
        self.assertTrue(IdmConfigParser.get_config_path() is None)