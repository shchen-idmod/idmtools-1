import os
from functools import partial

from config_update_parameters import config_update_params

from idmtools.builders import SweepArm, ArmType, ArmExperimentBuilder
from idmtools.core.platform_factory import Platform
from idmtools.managers import ExperimentManager
from idmtools_model_emod import EMODExperiment
from idmtools_model_emod.defaults import EMODSir

current_directory = os.path.dirname(os.path.realpath(__file__))
BIN_PATH = os.path.join(current_directory, "bin")
INPUT_PATH = os.path.join(current_directory, "inputs")

sim_duration = 10   # in years
num_seeds = 5

expname = 'example_arm_sweep_serialization'


def param_update(simulation, param, value):
    return simulation.set_parameter(param, value)


if __name__ == "__main__":
    platform = Platform('COMPS_SLURMCLUSTER')

    emod_version = '2.20.0'
    e = EMODExperiment.from_default(expname, default=EMODSir(), eradication_path=os.path.join(BIN_PATH, "Eradication"))
    e.demographics.clear()
    demo_file = os.path.join(INPUT_PATH, "single_node_demographics.json")
    e.demographics.add_demographics_from_file(demo_file)

    simulation = e.base_simulation
    sim = config_update_params(simulation)
    sim.set_parameter("Enable_Susceptibility_Scaling", 0)
    sim.set_parameter("Config_Name", "serializing sim")

    timesteps = [sim_duration * 365]
    sim.set_parameter("Serialization_Type", "TIMESTEP")
    sim.set_parameter("Serialization_Time_Steps", sorted(timesteps))

    start_day = sim.get_parameter("Start_Time")
    last_serialization_day = sorted(timesteps)[-1]
    end_day = start_day + last_serialization_day
    sim.set_parameter("Simulation_Duration", end_day)

    arm = SweepArm(type=ArmType.cross)
    set_Run_Number = partial(param_update, param="Run_Number")
    arm.add_sweep_definition(set_Run_Number, range(num_seeds))

    set_x_Temporary_Larval_Habitat = partial(param_update, param="x_Temporary_Larval_Habitat")
    arm.add_sweep_definition(set_x_Temporary_Larval_Habitat, [0.1, 0.2])

    builder = ArmExperimentBuilder()
    builder.add_arm(arm)
    e.builder = builder
    em = ExperimentManager(experiment=e, platform=platform)
    em.run()
    em.wait_till_done()