import os
import sys

from idmtools.assets import AssetCollection
from idmtools.core.platform_factory import Platform
from idmtools.entities import CommandLine
from idmtools.entities.command_task import CommandTask
from idmtools.entities.experiment import Experiment
from idmtools.entities.templated_simulation import TemplatedSimulations

if __name__ == "__main__":
    here = os.path.dirname(__file__)

    # Create a platform to run the workitem
    platform = Platform("CALCULON")

    # create commandline input for the task
    command = CommandLine("singularity exec ./Assets/covasim_ubuntu.sif python3 Assets/run_sim.py")
    task = CommandTask(command=command)
    ts = TemplatedSimulations(base_task=task)
    common_assets = AssetCollection.from_id("e614cb2d-442a-eb11-a2dd-c4346bcb7271", as_copy=True)

    task.common_assets = common_assets

    experiment = Experiment.from_task(task,
                                      name=os.path.split(sys.argv[0])[1],
                                      tags={
                                          'type': 'singularity',
                                          'description': 'run covasim'
                                      })
    experiment.add_asset(os.path.join("inputs", "run_sim.py"))
    experiment.run(wait_until_done=True)
