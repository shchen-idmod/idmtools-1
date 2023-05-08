"""
example.py shows how to run everything on slurm job in computation nodes
- First, it will run a slurm job for example.py to build experiment/simulations folder structure
- Second, another slurm job will be triggered by first slurm job to run experiment/simulations

Note, this example only run on Northwestern University QUEST cluster. if you want to run different slurm cluster, you
may need to change Platform parameters (i.e partition, account, etc.)
"""
import os
import sys
from functools import partial
from typing import Any, Dict

from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities import Suite
from idmtools.entities.experiment import Experiment
from idmtools.entities.simulation import Simulation
from idmtools.entities.templated_simulation import TemplatedSimulations
from idmtools_models.python.json_python_task import JSONConfiguredPythonTask

from idmtools_test import COMMON_INPUT_PATH

# job dir should be /home/username/example/slurm_job
job_directory = os.path.join(os.path.expanduser('~'), "example/slurm_job")

# Note, this example only runs on NU with their partition and acct
platform = Platform('SLURM_LOCAL', job_directory=job_directory, partition='b1139', time='10:00:00',
                        account='b1139')

task = JSONConfiguredPythonTask(script_path=os.path.join(COMMON_INPUT_PATH, "python", "model3.py"),
                                envelope="parameters", parameters=(dict(c=0)))
task.python_path = "python3"
ts = TemplatedSimulations(base_task=task)
ts.base_simulation.tags['tag1'] = 1
builder = SimulationBuilder()


def param_update(simulation: Simulation, param: str, value: Any) -> Dict[str, Any]:
    return simulation.task.set_parameter(param, value)

# Let's sweep the parameter 'a' for the values 0-2
builder.add_sweep_definition(partial(param_update, param="a"), range(3))

# Let's sweep the parameter 'b' for the values 0-4
builder.add_sweep_definition(partial(param_update, param="b"), range(5))
ts.add_builder(builder)

experiment = Experiment.from_template(ts, name="python example")
experiment.assets.add_directory(assets_directory=os.path.join(COMMON_INPUT_PATH, "python", "Assets"))

# Create suite
suite = Suite(name='Idm Suite')
suite.add_experiment(experiment)

suite.run(platform=platform, wait_until_done=True, max_running_jobs=10, retries=5)
sys.exit(0 if experiment.succeeded else -1)


