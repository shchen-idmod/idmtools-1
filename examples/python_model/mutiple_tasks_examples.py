import os

from idmtools.assets import Asset, AssetCollection
from idmtools.builders import StandAloneSimulationsBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.command_task import CommandTask

from idmtools.entities.experiment import Experiment
from idmtools.entities.templated_simulation import TemplatedSimulations

from idmtools_models.python.json_python_task import JSONConfiguredPythonTask


def run_example_PythonTask(ac_id):
    task = JSONConfiguredPythonTask(script_path=os.path.join("inputs", "task_model", "model_file.py"))

    ts = TemplatedSimulations(base_task=task)
    common_assets = AssetCollection.from_id(ac_id, platform=platform)
    sim = ts.new_simulation()
    experiment = Experiment(name="run_example_PythonTask", simulations=[sim], assets=common_assets)
    platform.run_items(experiment)
    platform.wait_till_done(experiment)


def run_example_CommandTask(ac_id):
    command = "python Assets/model_file.py"
    task = CommandTask(command=command)

    model_asset = Asset(absolute_path=os.path.join("inputs", "task_model", "model_file.py"))
    common_assets = AssetCollection.from_id(ac_id, platform=platform)
    common_assets.add_asset(model_asset)
    # create experiment from task
    experiment = Experiment.from_task(task, name="run_example_CommandTask", assets=common_assets)

    platform.run_items(experiment)
    platform.wait_till_done(experiment)

def run_pip_list():
    command = "Assets\\run.bat"
    task = CommandTask(command=command)
    ac = AssetCollection()
    model_asset = Asset(absolute_path=os.path.join("inputs", "task_model", "run.bat"))
    ac.add_asset(model_asset)
    # create experiment from task
    experiment = Experiment.from_task(task, name="run_pip_list", assets=ac)

    platform.run_items(experiment)
    platform.wait_till_done(experiment)

def run_example_task_from_template(ac_id):
    common_assets = AssetCollection.from_id(ac_id, platform=platform)
    task = JSONConfiguredPythonTask(script_path=os.path.join("inputs", "task_model", "model_file.py"),
                                    common_assets=common_assets, parameters=dict(c=0))
    ts = TemplatedSimulations(base_task=task)
    sim = ts.new_simulation()
    builder = StandAloneSimulationsBuilder()
    builder.add_simulation(sim)
    ts.add_builder(builder)

    # create experiment from task
    experiment = Experiment.from_template(ts, name="run_example_task_from_template")

    platform.run_items(experiment)
    platform.wait_till_done(experiment)


if __name__ == '__main__':
    platform = Platform('COMPS2')
    ac_id = "743df90e-2f57-ea11-a2bf-f0921c167862"
    if ac_id:
        run_example_CommandTask(ac_id)
        run_example_PythonTask(ac_id)
        run_example_task_from_template(ac_id)
        run_pip_list()
    else:
        print('Failed to generate asset collection!')
