from dramatiq import group
from dataclasses import dataclass
from idmtools.core import EntityStatus
from idmtools.entities import IExperiment, IPlatform
# we have to import brokers so that the proper configuration is achieved for redis
from idmtools.core import platform_factory
from idmtools_local.tasks.create_assest_task import AddAssetTask
from idmtools_local.tasks.create_experiement import CreateExperimentTask
from idmtools_local.tasks.create_simulation import CreateSimulationTask
from idmtools_local.tasks.run import RunTask


@dataclass
class LocalPlatform(IPlatform):
    """
    Represents the platform allowing to run simulations locally.
    """

    def retrieve_experiment(self, experiment_id):
        pass

    def get_assets_for_simulation(self, simulation, output_files):
        raise NotImplemented("Not implemented yet in the LocalPlatform")

    def restore_simulations(self, experiment):
        raise NotImplemented("Not implemented yet in the LocalPlatform")

    def refresh_experiment_status(self, experiment):
        for s in experiment.simulations:
            s.status = EntityStatus.SUCCEEDED

    def create_experiment(self, experiment: IExperiment):
        m = CreateExperimentTask.send(experiment.tags, experiment.simulation_type)
        eid = m.get_result(block=True)
        experiment.uid = eid
        self.send_assets_for_experiment(experiment)

    def send_assets_for_experiment(self, experiment):
        # Go through all the assets
        messages = []
        for asset in experiment.assets:
            messages.append(
                AddAssetTask.message(experiment.uid, asset.filename, path=asset.relative_path,
                                     contents=asset.content.decode("utf-8")))
        group(messages).run().wait()

    def send_assets_for_simulation(self, simulation):
        # Go through all the assets
        messages = []
        for asset in simulation.assets:
            messages.append(
                AddAssetTask.message(simulation.experiment.uid, asset.filename, path=asset.relative_path,
                                     contents=asset.content.decode("utf-8"), simulation_id=simulation.uid))
        group(messages).run().wait()

    def create_simulations(self, simulations_batch):
        ids = []
        for simulation in simulations_batch:
            m = CreateSimulationTask.send(simulation.experiment.uid, simulation.tags)
            sid = m.get_result(block=True)
            simulation.uid = sid
            self.send_assets_for_simulation(simulation)
            ids.append(sid)
        return ids

    def run_simulations(self, experiment: IExperiment):
        for simulation in experiment.simulations:
            RunTask.send(simulation.experiment.command.cmd, simulation.experiment.uid, simulation.uid)


platform_factory.register_type(LocalPlatform)
