import os
import pytest
import unittest
from idmtools.core import EntityStatus
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
from idmtools_models.python.json_python_task import JSONConfiguredPythonTask
from idmtools_platform_comps.utils.assetize_output.assetize_output import AssetizeOutput
from idmtools_platform_comps.utils.assetize_output.assetize_ssmt_script import is_file_excluded
from idmtools_test import COMMON_INPUT_PATH
from idmtools_test.utils.test_task import TestTask


@pytest.mark.comps
class TestAssetizeOutput(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.case_name = os.path.basename(__file__) + "--" + self._testMethodName

    @pytest.mark.smoke
    def test_experiment_can_be_watched(self):
        e = Experiment.from_task(task=TestTask())
        ao = AssetizeOutput()
        ao.from_items(e)
        self.assertEqual(1, len(ao.related_experiments))
        self.assertEqual(ao.related_experiments[0], e)

    @pytest.mark.smoke
    def test_exclude(self):
        patterns = ['**StdOut.txt', '**StdErr.txt', '**.log']
        dummy_files = [
            'ABc/StdOut.txt',
            'b.py',
            'ABc/stdOut.txt',
            'ABc/stderr.txt',
            'ABc/123/stdout.txt',
            'ABc/123/stdout.err',
            'ABc/123/StdErr.err',
            'comps.log',
            'logs/idmtools.log'
        ]
        filtered_list = [f for f in dummy_files if not is_file_excluded(f, patterns)]
        self.assertEqual(len(filtered_list), 3)
        self.assertIn('b.py', filtered_list)
        self.assertIn('ABc/123/stdout.err', filtered_list)
        self.assertIn('ABc/123/StdErr.err', filtered_list)

    @pytest.mark.smoke
    def test_experiment_precreate_fails_if_no_watched_items(self):
        ao = AssetizeOutput()
        self.assertEqual(0, len(ao.related_experiments))
        with self.assertRaises(ValueError) as er:
            ao.pre_creation(None)
        self.assertEqual(er.exception.args[0], "You must specify at least one item to watch")

    @pytest.mark.smoke
    @pytest.mark.serial
    def test_experiment_default_pattern_if_none_specified(self):
        e = Experiment.from_task(task=TestTask())
        e.simulations[0].status = EntityStatus.CREATED
        e.uid = '095565e833818aab3340e802512c32ff'
        ao = AssetizeOutput()
        ao.from_items(e)
        self.assertEqual(1, len(ao.related_experiments))
        self.assertEqual(ao.related_experiments[0], e)
        ao.pre_creation(None)
        self.assertEqual(1, len(ao.file_patterns))
        self.assertEqual("**", ao.file_patterns[0])
        print(e.id)
        self.assertEqual(ao.create_command(), 'python3 Assets/assetize_ssmt_script.py --file-pattern "**" --exclude-pattern "StdErr.txt" --exclude-pattern "StdOut.txt" --exclude-pattern "WorkOrder.json" --exclude-pattern "*.log" --asset-tag "AssetizedOutputfromFromExperiment=095565e833818aab3340e802512c32ff" --simulation-prefix-format-str "{simulation.id}"')
        ao.verbose = True
        self.assertEqual(ao.create_command(), 'python3 Assets/assetize_ssmt_script.py --file-pattern "**" --exclude-pattern "StdErr.txt" --exclude-pattern "StdOut.txt" --exclude-pattern "WorkOrder.json" --exclude-pattern "*.log" --asset-tag "AssetizedOutputfromFromExperiment=095565e833818aab3340e802512c32ff" --simulation-prefix-format-str "{simulation.id}" --verbose')
        ao.clear_exclude_patterns()
        self.assertEqual(ao.create_command(), 'python3 Assets/assetize_ssmt_script.py --file-pattern "**" --asset-tag "AssetizedOutputfromFromExperiment=095565e833818aab3340e802512c32ff" --simulation-prefix-format-str "{simulation.id}" --verbose')

        def pre_run_dummy():
            pass

        def entity_filter_dummy(item):
            return True

        def another_pre_run_dummy():
            pass
        ao.pre_run_functions.append(pre_run_dummy)
        ao.entity_filter_function = entity_filter_dummy
        ao.pre_creation(None)
        self.assertEqual(len(ao.assets), 3)
        self.assertIn("pre_run.py", [f.filename for f in ao.assets])
        self.assertIn("entity_filter_func.py", [f.filename for f in ao.assets])
        self.assertEqual(ao.create_command(), 'python3 Assets/assetize_ssmt_script.py --file-pattern "**" --asset-tag "AssetizedOutputfromFromExperiment=095565e833818aab3340e802512c32ff" --simulation-prefix-format-str "{simulation.id}" --pre-run-func pre_run_dummy --entity-filter-func entity_filter_dummy --verbose')

        ao.pre_run_functions.append(another_pre_run_dummy)
        self.assertEqual(ao.create_command(), 'python3 Assets/assetize_ssmt_script.py --file-pattern "**" --asset-tag "AssetizedOutputfromFromExperiment=095565e833818aab3340e802512c32ff" --simulation-prefix-format-str "{simulation.id}" --pre-run-func pre_run_dummy --pre-run-func another_pre_run_dummy --entity-filter-func entity_filter_dummy --verbose')

    def test_comps_simple(self):
        platform = Platform("COMPS2")
        task = JSONConfiguredPythonTask(script_path=os.path.join(COMMON_INPUT_PATH, "python", "model1.py"), parameters=dict(a=1))
        e = Experiment.from_task(name=self.case_name, task=task)
        ao = AssetizeOutput(name=self.case_name, verbose=True)
        ao.from_items(e)
        ao.run(wait_on_done=True)

        self.assertTrue(e.succeeded)
        self.assertTrue(ao.succeeded)

    def test_experiment(self):
        ao = AssetizeOutput(name=self.case_name, related_experiments=['9311af40-1337-ea11-a2be-f0921c167861'], file_patterns=["**/a.csv"], verbose=True)
        ac = ao.run(wait_on_done=True, platform=Platform("COMPS2"))

        self.assertTrue(ao.succeeded)
        self.assertIsNotNone(ac)

        self.assertEqual(ac, ao.asset_collection)
        filelist = [f.filename for f in ac]
        self.assertEqual(9, len(filelist))

    def test_experiment_sim_prefix(self):
        ao = AssetizeOutput(name=self.case_name, related_experiments=['9311af40-1337-ea11-a2be-f0921c167861'], simulation_prefix_format_str="{simulation.state}/{simulation.id}", file_patterns=["**/a.csv"], verbose=True)
        ac = ao.run(wait_on_done=True, platform=Platform("COMPS2"))

        self.assertTrue(ao.succeeded)
        self.assertIsNotNone(ac)

        self.assertEqual(ac, ao.asset_collection)
        filelist = [f.filename for f in ac]
        self.assertEqual(9, len(filelist))

    def test_simulation(self):
        ao = AssetizeOutput(name=self.case_name, related_simulations=['9d11af40-1337-ea11-a2be-f0921c167861'], file_patterns=["**/*.csv"], verbose=True)
        ac = ao.run(wait_on_done=True, platform=Platform("COMPS2"))

        self.assertTrue(ao.succeeded)
        self.assertIsNotNone(ac)

        self.assertEqual(ac, ao.asset_collection)
        filelist = [f.filename for f in ac]
        self.assertEqual(3, len(filelist))

    def test_workitem(self):
        ao = AssetizeOutput(name=self.case_name, related_work_items=['a6d11db7-1603-e911-80ca-f0921c167866'], file_patterns=["*.png"], verbose=True)
        ac = ao.run(wait_on_done=True, platform=Platform("COMPS2"))

        self.assertTrue(ao.succeeded)
        self.assertIsNotNone(ac)

        self.assertEqual(ac, ao.asset_collection)
        filelist = [f.filename for f in ac]
        self.assertEqual(1, len(filelist))

        with self.subTest("test_workitem_prefix"):

            ao2 = AssetizeOutput(name=self.case_name, related_work_items=['a6d11db7-1603-e911-80ca-f0921c167866', ao], file_patterns=["**.txt"], exclude_patterns=['WorkOrder.json'], verbose=True, work_item_prefix_format_str="{work_item.name}")
            ac = ao2.run(wait_on_done=True, platform=Platform("COMPS2"))
            self.assertTrue(ao2.succeeded)
            self.assertIsNotNone(ac)

            self.assertEqual(ac, ao2.asset_collection)
            filelist = [f.filename for f in ac]
            self.assertEqual(4, len(filelist))

    def test_filter_ac(self):
        ao = AssetizeOutput(name=self.case_name, related_asset_collections=['2b53af74-2b4a-e711-80c1-f0921c167860'], file_patterns=["**/libvectorstats.dll"], verbose=True)
        ac = ao.run(wait_on_done=True, platform=Platform("COMPS2"))

        self.assertTrue(ao.succeeded)
        self.assertIsNotNone(ac)

        self.assertEqual(ac, ao.asset_collection)
        filelist = [f.filename for f in ac]
        self.assertEqual(1, len(filelist))

    def test_dry_run(self):
        ao = AssetizeOutput(name=self.case_name, related_simulations=['9d11af40-1337-ea11-a2be-f0921c167861'], related_asset_collections=['2b53af74-2b4a-e711-80c1-f0921c167860'], verbose=True, dry_run=True)
        ac = ao.run(wait_on_done=True, platform=Platform("COMPS2"))

        self.assertTrue(ao.succeeded)
        self.assertIsNone(ac)

