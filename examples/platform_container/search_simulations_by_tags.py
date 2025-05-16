# This example demonstrates how to search simulations with tags
import os
import sys
from functools import partial
from typing import Any, Dict
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
from idmtools.entities.simulation import Simulation
from idmtools.entities.templated_simulation import TemplatedSimulations
from idmtools_models.python.json_python_task import JSONConfiguredPythonTask

platform = Platform("Container", job_directory="DEST")
# Define path to assets directory
assets_directory = os.path.join("..", "python_model", "inputs", "python", "Assets")
# Define task
task = JSONConfiguredPythonTask(script_path=os.path.join(assets_directory, "model.py"), parameters=(dict(c=0)))
# Define templated simulation
ts = TemplatedSimulations(base_task=task)
ts.base_simulation.tags['tag1'] = 1
# Define builder
builder = SimulationBuilder()

# Define partial function to update parameter
def param_update(simulation: Simulation, param: str, value: Any) -> Dict[str, Any]:
    return simulation.task.set_parameter(param, value)

# Let's sweep the parameter 'a' for the values 0-2
builder.add_sweep_definition(partial(param_update, param="a"), range(3))

# Let's sweep the parameter 'b' for the values 0-4
builder.add_sweep_definition(partial(param_update, param="b"), range(5))
ts.add_builder(builder)

# Create Experiment using template builder
experiment = Experiment.from_template(ts, name="python example")

# And all files from assets_directory to experiment folder
experiment.assets.add_directory(assets_directory=assets_directory)

experiment.run(platform=platform, wait_until_done=True)

# search simulations with matched tags
# First case: return matched simulation ids in list
simulation_ids = experiment.simulations_with_tags(tags={"a": 2, "b": 1})
# Second case: return matched simulation objects in list (entity_type=True means return Simulation Object instead of id)
simulations = experiment.simulations_with_tags(tags={"a": 2, "b": 1}, entity_type=True)

sys.exit(0 if experiment.succeeded else -1)





