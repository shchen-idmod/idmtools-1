import copy
import typing
from abc import ABC

from more_itertools import grouper

from idmtools.assets.AssetCollection import AssetCollection
from idmtools.core import EntityContainer, IAssetsEnabled, INamedEntity
from idmtools.utils.decorators import pickle_ignore_fields

if typing.TYPE_CHECKING:
    from idmtools.core.types import TSimulation, TSimulationClass, TCommandLine


@pickle_ignore_fields(["simulations", "builder"])
class IExperiment(IAssetsEnabled, INamedEntity, ABC):
    """
    Represents a generic Experiment.
    This class needs to be implemented for each model type with specifics.
    """

    def __init__(self, name, simulation_type: 'TSimulationClass' = None, assets: 'AssetCollection' = None,
                 base_simulation: 'TSimulation' = None, command: 'TCommandLine' = None):
        """
        Constructor.
        Args:
            name: The experiment name.
            simulation_type: A class to initialize the simulations that will be created for this experiment
            assets: The asset collection for assets global to this experiment
            base_simulation: Optional a simulation that will be the base for all simulations created for this experiment
            command: Command to run on simulations
        """
        IAssetsEnabled.__init__(self, assets=assets)
        INamedEntity.__init__(self, name=name)

        self.command = command
        self.simulation_type = simulation_type
        self.name = name
        self.builder = None
        self.suite_id = None
        self.simulations = EntityContainer()

        # Take care of the base simulation
        if base_simulation:
            self.base_simulation = base_simulation
        elif simulation_type:
            self.base_simulation = simulation_type()
        else:
            raise Exception("A `base_simulation` or `simulation_type` needs to be provided to the Experiment object!")

    def __repr__(self):
        return f"<Experiment: {self.uid} - {self.name} / Sim count {len(self.simulations)}>"

    def display(self):
        from idmtools.utils.display import display, experiment_table_display
        display(self, experiment_table_display)

    def batch_simulations(self, batch_size=5):
        if not self.builder:
            yield (self.simulation(),)
            return

        for groups in grouper(self.builder, batch_size):
            sims = []
            for simulation_functions in filter(None, groups):
                simulation = self.simulation()
                tags = {}

                for func in simulation_functions:
                    new_tags = func(simulation=simulation)
                    if new_tags:
                        tags.update(new_tags)

                simulation.tags = tags
                sims.append(simulation)

            yield sims

    def simulation(self):
        """
        Returns a new simulation object.
        The simulation will be copied from the base simulation of the experiment.
        Returns: The created simulation
        """
        sim = copy.deepcopy(self.base_simulation)
        sim.experiment = self
        sim.assets = copy.deepcopy(self.base_simulation.assets)
        return sim

    def pre_creation(self):
        self.gather_assets()

    def post_setstate(self):
        self.simulations = EntityContainer()

    @property
    def done(self):
        return all([s.done for s in self.simulations])

    @property
    def succeeded(self):
        return all([s.succeeded for s in self.simulations])

    @property
    def simulation_count(self):
        return len(self.simulations)
