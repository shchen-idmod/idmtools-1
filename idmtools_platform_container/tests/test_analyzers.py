import os
import unittest
from functools import partial
from typing import Any, Dict
import pytest
from idmtools.analysis.analyze_manager import AnalyzeManager
from idmtools.builders import SimulationBuilder
from idmtools.core import ItemType
from idmtools.entities import IAnalyzer
from idmtools.entities.experiment import Experiment
from idmtools.entities.templated_simulation import TemplatedSimulations
from idmtools_models.python.json_python_task import JSONConfiguredPythonTask
from idmtools_platform_container.container_platform import ContainerPlatform
from idmtools.entities.simulation import Simulation
current_directory = os.path.dirname(os.path.realpath(__file__))
param_a = partial(JSONConfiguredPythonTask.set_parameter_sweep_callback, param="a")


class AddAnalyzer(IAnalyzer):
    """
    Add Analyzer
    A simple base class to add analyzers.

    """

    def __init__(self, filenames=["config.json"]):
        super().__init__(filenames=filenames)

    def map(self, data, item):
        a = data[self.filenames[0]]['parameters']["a"]
        b = data[self.filenames[0]]['parameters']["b"]
        result = a + b
        return result

    def reduce(self, data):
        print(f'Sum: {str(data.values())}')
        value = sum(data.values())
        return value


@pytest.mark.analysis
@pytest.mark.serial
class TestContainerPlatformAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        case_name = os.path.basename(__file__) + "--" + cls.__name__
        job_directory = "DEST"
        cls.platform = ContainerPlatform(job_directory=job_directory)

        builder = SimulationBuilder()
        # Sweep parameter "a"
        def param_update(simulation: Simulation, param: str, value: Any) -> Dict[str, Any]:
            return simulation.task.set_parameter(param, value)

        builder.add_sweep_definition(partial(param_update, param="a"), range(3))
        builder.add_sweep_definition(partial(param_update, param="b"), range(5))

        task = JSONConfiguredPythonTask(script_path=os.path.join("inputs", "model3.py"),
                                        envelope="parameters", parameters=(dict(c=0)))
        task.python_path = "python3"
        tags = {"string_tag": "test", "number_tag": 123}
        ts = TemplatedSimulations(base_task=task)
        ts.add_builder(builder)
        experiment = Experiment.from_template(ts, name=case_name, tags=tags)
        experiment.assets.add_directory(assets_directory=os.path.join("inputs", "Assets"))
        experiment.run(True, platform=cls.platform)
        cls.exp_id = experiment.uid

    def test_AddAnalyzer(self):
        self.case_name = os.path.basename(__file__)
        analyzers = [AddAnalyzer(filenames=['config.json'])]

        am = AnalyzeManager(platform=self.platform, ids=[(self.exp_id, ItemType.EXPERIMENT)], analyzers=analyzers)
        am.analyze()
        print(analyzers[0].results)
        self.assertEqual(analyzers[0].results, 45)