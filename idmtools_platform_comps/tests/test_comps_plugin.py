import tempfile

import os

import unittest
import dataclasses

import pytest

from idmtools import IdmConfigParser
from idmtools.core import CacheEnabled
from idmtools.entities.iplatform import IPlatform
from idmtools.entities.platform_requirements import PlatformRequirements
from idmtools.registry.platform_specification import PlatformPlugins
from idmtools_platform_comps.comps_platform import COMPSPlatform
from idmtools_platform_comps.plugin_info import COMPSPlatformSpecification


class TestCompsPlugin(unittest.TestCase):
    @pytest.mark.smoke
    def test_comps_in_entrypoints(self):
        """
        This test requires the package is installed first. In then confirms that COMPS is detected by the
        PlatformPlugins manager
        """
        pl = PlatformPlugins()
        self.assertIn('COMPS', pl.get_plugin_map().keys())

    def test_platform_short_name_is_comps(self):
        spec = COMPSPlatformSpecification()
        self.assertEqual("COMPS", spec.get_name())

    def test_example_config_contains_all_config_options(self):
        """
        Ensures all the example config contains all our possible config options

        """
        fields = dataclasses.fields(COMPSPlatform)
        exclude_fields = dataclasses.fields(IPlatform) + dataclasses.fields(CacheEnabled)

        spec = COMPSPlatformSpecification()
        example_config = spec.example_configuration()
        for field in fields:
            # skip private fields and not picklable as they are most lik
            if field.name[0] != '_' and field not in exclude_fields and not field.metadata.get('pickle_ignore', False) \
                    and field.name != 'docker_image':
                self.assertIn(field.name, example_config)

    @pytest.mark.comps
    def test_platform_aliases(self):
        from idmtools.core.platform_factory import Platform
        org_directory = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmpdirname:
                os.chdir(tmpdirname)
                IdmConfigParser.clear_instance()

                with Platform("BAYESIAN") as comps2:
                    self.assertEqual(comps2.endpoint, "https://comps2.idmod.org")
                    self.assertEqual(comps2.environment.upper(), "BAYESIAN")

                with Platform("SlurmStage") as comps2:
                    self.assertEqual(comps2.endpoint, "https://comps2.idmod.org")
                    self.assertEqual(comps2.environment.upper(), "SLURMSTAGE")
        finally:
            os.chdir(org_directory)
