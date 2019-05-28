import copy

from assets.AssetCollection import AssetCollection
from interfaces.IEntity import IEntity
from interfaces.ISimulation import ISimulation


class IExperiment(IEntity):
    """
    Represents a generic Simulation.
    This class needs to be implemented for each model type with specifics.
    """

    def __init__(self, name, simulation_type: type, assets: AssetCollection = None,
                 base_simulation: ISimulation = None):
        """
        Constructor.
        Args:
            name: The experiment name.
            simulation_type: A class to initialize the simulations that will be created for this experiment
            assets: The asset collection for assets global to this experiment
            base_simulation: Optional a simulation that will be the base for all simulations created for this experiment
        """
        super().__init__(assets=assets)
        self.simulation_type = simulation_type
        self.simulations = []
        self.name = name
        self.base_simulation = base_simulation or self.simulation_type()
        self.builder = None

    def __repr__(self):
        return f"<Experiment: {self.uid} - {self.name} / Sim count {len(self.simulations)}>"

    def execute_builder(self):
        """
        Execute the builder of this experiment, generating all the simulations.
        """
        for simulation_functions in self.builder:
            simulation = self.simulation()
            tags = {}

            for func in simulation_functions:
                tags.update(func(simulation=simulation))

            simulation.tags = tags

    def simulation(self):
        """
        Returns a new simulation object.
        The simulation will be copied from the base simulation of the experiment.
        Returns: The created simulation
        """
        sim = copy.deepcopy(self.base_simulation)

        sim.experiment_id = self.uid
        self.simulations.append(sim)
        return sim
