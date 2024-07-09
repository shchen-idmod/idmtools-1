import os
import sys

from examples.platform_container.utils.utils import get_wrapper_script_as_string
from idmtools.assets import Asset, AssetCollection
from idmtools.core.platform_factory import Platform
from idmtools.entities.command_task import CommandTask
from idmtools.entities.experiment import Experiment
from idmtools_models.templated_script_task import TemplatedScriptTask, get_script_wrapper_unix_task


def run_with_extra_package():
    platform = Platform('CONTAINER', job_directory="DEST", new_container=True)
    command = "python Assets/model_file.py"
    task = CommandTask(command=command)

    wrapper_task: TemplatedScriptTask = get_script_wrapper_unix_task(task, template_content=get_wrapper_script_as_string(['astor']))
    model_asset = Asset(absolute_path=os.path.join("inputs", "extra_packages", "model_file.py"))
    common_assets = AssetCollection()
    common_assets.add_asset(model_asset)
    experiment = Experiment.from_task(wrapper_task,  name="run_with_new_container", assets=common_assets)
    experiment.run(wait_until_done=True)
    sys.exit(0 if experiment.succeeded else -1)


if __name__ == '__main__':
    run_with_extra_package()
