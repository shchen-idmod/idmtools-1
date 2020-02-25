import json
import os
import sys

import pytest
from idmtools.analysis.platform_anaylsis import PlatformAnalysis
from idmtools.core import ItemType
from idmtools.core.platform_factory import Platform
from idmtools_test.utils.itest_with_persistence import ITestWithPersistence
from idmtools_test.utils.utils import del_folder

analyzer_path = os.path.join(os.path.dirname(__file__), "..", "inputs")
sys.path.insert(0, analyzer_path)
from PopulationAnalyzer import PopulationAnalyzer  # noqa
from AdultVectorsAnalyzer import AdultVectorsAnalyzer  # noqa


@pytest.mark.comps
@pytest.mark.ssmt
class TestSSMTAnalysis(ITestWithPersistence):

    def setUp(self) -> None:
        self.case_name = os.path.basename(__file__) + "--" + self._testMethodName
        print(self.case_name)
        self.platform = Platform('COMPS2')

    # test using SSMTAnalysis to run PopulationAnalyzer in comps's SSMT DockerWorker
    def test_ssmt_analysis_PopulationAnalyzer(self):
        experiment_id = "8bb8ae8f-793c-ea11-a2be-f0921c167861"
        analysis = PlatformAnalysis(platform=self.platform,
                                    experiment_ids=[experiment_id],
                                    analyzers=[PopulationAnalyzer],
                                    analyzers_args=[{'name': 'anything'}],
                                    analysis_name=self.case_name,
                                    tags={'idmtools': self._testMethodName, 'WorkItem type': 'Docker'})

        analysis.analyze(check_status=True)
        wi = analysis.get_work_item()

        # validate output files
        local_output_path = "output"
        del_folder(local_output_path)
        out_filenames = ["output/population.png", "output/population.json", "WorkOrder.json"]
        self.platform.get_files_by_id(wi.uid, ItemType.WORKFLOW_ITEM, out_filenames, local_output_path)

        file_path = os.path.join(local_output_path, str(wi.uid))
        self.assertTrue(os.path.exists(os.path.join(file_path, "output", "population.png")))
        self.assertTrue(os.path.exists(os.path.join(file_path, "output", "population.json")))
        self.assertTrue(os.path.exists(os.path.join(file_path, "WorkOrder.json")))
        worker_order = json.load(open(os.path.join(file_path, "WorkOrder.json"), 'r'))
        print(worker_order)
        self.assertEqual(worker_order['WorkItem_Type'], "DockerWorker")
        execution = worker_order['Execution']
        self.assertEqual(execution['Command'],
                         "python platform_analysis_bootstrap.py " + experiment_id + " PopulationAnalyzer.PopulationAnalyzer COMPS2")

    # test using SSMTAnalysis to run multiple analyzers in comps's SSMT DockerWorker
    def test_ssmt_analysis_multiple_analyzers(self):
        experiment_id = "8bb8ae8f-793c-ea11-a2be-f0921c167861"
        analysis = PlatformAnalysis(platform=self.platform,
                                    experiment_ids=[experiment_id],
                                    analyzers=[PopulationAnalyzer, AdultVectorsAnalyzer],
                                    analyzers_args=[{'name': 'anything'}, {'name': "adult test"}],
                                    analysis_name=self.case_name,
                                    tags={'idmtools': self._testMethodName, 'WorkItem type': 'Docker'})

        analysis.analyze(check_status=True)
        wi = analysis.get_work_item()

        # validate output files
        local_output_path = "output"
        del_folder(local_output_path)
        out_filenames = ["output/population.png", "output/population.json",
                         "output/adult_vectors.json", "output/adult_vectors.png", "WorkOrder.json"]
        self.platform.get_files_by_id(wi.uid, ItemType.WORKFLOW_ITEM, out_filenames,
                                      local_output_path)

        file_path = os.path.join(local_output_path, str(wi.uid))
        self.assertTrue(os.path.exists(os.path.join(file_path, "output", "population.png")))
        self.assertTrue(os.path.exists(os.path.join(file_path, "output", "population.json")))
        self.assertTrue(os.path.exists(os.path.join(file_path, "output", "adult_vectors.png")))
        self.assertTrue(os.path.exists(os.path.join(file_path, "output", "adult_vectors.json")))

        self.assertTrue(os.path.exists(os.path.join(file_path, "WorkOrder.json")))
        worker_order = json.load(open(os.path.join(file_path, "WorkOrder.json"), 'r'))
        print(worker_order)
        self.assertEqual(worker_order['WorkItem_Type'], "DockerWorker")
        execution = worker_order['Execution']
        self.assertEqual(execution['Command'],
                         "python platform_analysis_bootstrap.py " + experiment_id + " PopulationAnalyzer.PopulationAnalyzer,AdultVectorsAnalyzer.AdultVectorsAnalyzer COMPS2")

    # test using SSMTAnalysis to run multiple experiments in comps's SSMT DockerWorker
    def test_ssmt_analysis_multiple_experiments(self):
        exp_id1 = "8bb8ae8f-793c-ea11-a2be-f0921c167861"
        exp_id2 = "4ea96af7-1549-ea11-a2be-f0921c167861"
        experiment_id = [exp_id1, exp_id2]
        analysis = PlatformAnalysis(platform=self.platform,
                                    experiment_ids=experiment_id,
                                    analyzers=[PopulationAnalyzer],
                                    analyzers_args=[{'name': 'anything'}],
                                    analysis_name=self.case_name,
                                    tags={'idmtools': self._testMethodName, 'WorkItem type': 'Docker'})

        analysis.analyze(check_status=True)
        wi = analysis.get_work_item()

        # validate output files
        local_output_path = "output"
        del_folder(local_output_path)
        out_filenames = ["output/population.png", "output/population.json", "WorkOrder.json"]
        self.platform.get_files_by_id(wi.uid, ItemType.WORKFLOW_ITEM, out_filenames, local_output_path)

        file_path = os.path.join(local_output_path, str(wi.uid))
        self.assertTrue(os.path.exists(os.path.join(file_path, "output", "population.png")))
        self.assertTrue(os.path.exists(os.path.join(file_path, "output", "population.json")))
        self.assertTrue(os.path.exists(os.path.join(file_path, "WorkOrder.json")))
        worker_order = json.load(open(os.path.join(file_path, "WorkOrder.json"), 'r'))
        print(worker_order)
        self.assertEqual(worker_order['WorkItem_Type'], "DockerWorker")
        execution = worker_order['Execution']
        self.assertEqual(execution['Command'],
                         "python platform_analysis_bootstrap.py " + exp_id1 + "," + exp_id2 + " PopulationAnalyzer.PopulationAnalyzer COMPS2")
