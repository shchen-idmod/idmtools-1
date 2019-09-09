import unittest.mock
import pytest
from dataclasses import fields
from idmtools.config import IdmConfigParser
from idmtools.core.PlatformFactory import Platform
from idmtools_test.utils.ITestWithPersistence import ITestWithPersistence
from idmtools_test.utils.confg_local_runner_test import get_test_local_env_overrides


class TestPlatformFactory(ITestWithPersistence):
    def setUp(self):
        super().setUp()
        IdmConfigParser.clear_instance()

    def tearDown(self):
        super().tearDown()

    def test_get_block(self):
        entries = IdmConfigParser.get_block('COMPS2')
        self.assertEqual(entries['endpoint'], 'https://comps2.idmod.org')

    def test_block_not_exits(self):
        with self.assertRaises(ValueError) as context:
            Platform('NOTEXISTS')  # noqa:F841
        self.assertEqual("Block 'NOTEXISTS' doesn't exist!", str(context.exception.args[0]))

    def test_bad_type(self):
        with self.assertRaises(ValueError) as context:
            Platform('BADTYPE')  # noqa:F841
        self.assertTrue("Bad is an unknown Platform Type.Supported platforms are" in str(context.exception.args[0]))

    @pytest.mark.docker
    @pytest.mark.comps
    @unittest.mock.patch('idmtools_platform_comps.COMPSPlatform.COMPSPlatform._login', side_effect=lambda: True)
    def test_create_from_block(self, mock_login):
        p1 = Platform('Custom_Local', **get_test_local_env_overrides())
        self.assertEqual(p1.__class__.__name__, 'LocalPlatform')

        p2 = Platform('COMPS2')
        self.assertEqual(p2.__class__.__name__, 'COMPSPlatform')
        self.assertEqual(mock_login.call_count, 1)

        p3 = Platform('Test')
        self.assertEqual(p3.__class__.__name__, 'TestPlatform')

    @pytest.mark.docker
    @pytest.mark.comps
    @unittest.mock.patch('idmtools_platform_comps.COMPSPlatform.COMPSPlatform._login', side_effect=lambda: True)
    def test_platform_factory(self, mock_login):
        platform1 = Platform('COMPS')
        self.assertEqual(platform1.__class__.__name__, 'COMPSPlatform')
        self.assertEqual(mock_login.call_count, 1)

        platform2 = Platform('Local', **get_test_local_env_overrides())
        self.assertEqual(platform2.__class__.__name__, 'LocalPlatform')

        platform3 = Platform('Test')
        self.assertEqual(platform3.__class__.__name__, 'TestPlatform')

    @pytest.mark.comps
    @unittest.mock.patch('idmtools_platform_comps.COMPSPlatform.COMPSPlatform._login', side_effect=lambda: True)
    def test_COMPSPlatform(self, mock_login):
        platform = Platform('COMPS2')
        self.assertEqual(mock_login.call_count, 1)
        members = platform.__dict__

        field_name = {f.name for f in fields(platform)}
        keys = field_name.intersection(members.keys())
        kwargs = {key: members[key] for key in keys}

        platform2 = Platform('COMPS', **kwargs)
        self.assertEqual(mock_login.call_count, 2)
        self.assertEqual(platform, platform2)

    @pytest.mark.docker
    def test_LocalPlatform(self):
        platform = Platform('Custom_Local', **get_test_local_env_overrides())
        members = platform.__dict__

        field_name = {f.name for f in fields(platform)}
        keys = field_name.intersection(members.keys())
        kwargs = {key: members[key] for key in keys}

        platform2 = Platform('Local', **kwargs)
        self.assertEqual(platform, platform2)

    def test_TestPlatform(self):
        platform = Platform('Test')
        members = platform.__dict__

        field_name = {f.name for f in fields(platform)}
        keys = field_name.intersection(members.keys())
        kwargs = {key: members[key] for key in keys}

        platform2 = Platform('Test', **kwargs)
        self.assertEqual(platform, platform2)
