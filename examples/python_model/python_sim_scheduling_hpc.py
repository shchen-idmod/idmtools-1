# In this example, we will demonstrate how to run use WorkOrder.json to create simulation in mshpc cluster
# if use WorkOrder.json correctly, it will create simulations based on the Command in WorkOrder.json. all commands from
# task will get ignored

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
from idmtools_platform_comps.utils.scheduling import add_work_order

# first define our base task. please see the detail explanation in examples/python_models/python_sim.py
# if we do not use WorkOrder.json, this task will create simulation command run as "python Assets/model.py" in comps
# but for this example, we will use WorkOrder.json to override this command, so here the task's script can be anything
task = JSONConfiguredPythonTask(script_path=os.path.join("inputs", "python_model_with_deps", "Assets", "model.py"),
                                parameters=(dict(c=0)))

# now let's use this task to create a TemplatedSimulation builder. This will build new simulations from sweep builders
# we will define later. We can also use it to manipulate the base_task or the base_simulation
ts = TemplatedSimulations(base_task=task)

# We can define common metadata like tags across all the simulations using the base_simulation object
ts.base_simulation.tags['tag1'] = 1

# load WorkOrder.json file from local to each simulation via task. the actual command in comps will contain in this file
add_work_order(ts, file_path=os.path.join("inputs", "scheduling", "hpc", "WorkOrder.json"))

# Since we have our templated simulation object now, let's define our sweeps
# To do that we need to use a builder
builder = SimulationBuilder()


# define an utility function that will update a single parameter at a
# time on the model and add that param/value pair as a tag on our simulation.
def param_update(simulation: Simulation, param: str, value: Any) -> Dict[str, Any]:
    """
    This function is called during sweeping allowing us to pass the generated sweep values to our Task Configuration

    We always receive a Simulation object. We know that simulations all have tasks and that for our particular set
    of simulations they will all include JSONConfiguredPythonTask. We configure the model with calls to set_parameter
    to update the config. In addition, we are can return a dictionary of tags to add to the simulations so we return
    the output of the 'set_parameter' call since it returns the param/value pair we set

    Args:
        simulation: Simulation we are configuring
        param: Param string passed to use
        value: Value to set param to

    Returns:

    """
    return simulation.task.set_parameter(param, value)


# now add the sweep to our builder
builder.add_sweep_definition(partial(param_update, param="a"), range(3))
builder.add_sweep_definition(partial(param_update, param="b"), [1, 2, 3])
ts.add_builder(builder)

# Now we can create our Experiment using our template builder
experiment = Experiment.from_template(ts, name=os.path.split(sys.argv[0])[1])
# Add our own custom tag to simulation
experiment.tags["tag1"] = 1
# And maybe some custom Experiment Level Assets
experiment.assets.add_directory(assets_directory=os.path.join("inputs", "python_model_with_deps", "Assets"))

with Platform('IDMCloud') as platform:
    # Call run() with 'scheduling=True' to run simulations with scheduling using WorkOrder.json(loaded above)
    # There are few ways to schedule computation resources in COMPS:
    #    1. add_work_order() method to add WorkOrder.json file to simulations as transient asset
    #    2. add_schedule_config() method can be used to add dynamic WorkOrder.json to simulations as transient asset
    #    3. add additional parameters to Platform creation with Platform(**kwargs) in kwargs
    #    4. idmtools.ini
    # the order of precedence is WorkOrder.json > Platform() > idmtools.ini
    # with experiment.run method, you can also passin other options like 'priority=Highest' here to override any
    # priority value either passed in from idmtools.ini or defined in Platform(**kwargs)
    experiment.run(True, priority='Highest')
    # use system status as the exit code
    sys.exit(0 if experiment.succeeded else -1)
