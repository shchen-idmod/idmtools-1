import base64
import dataclasses
import os
from typing import Optional

from dramatiq import group
from dataclasses import dataclass
from idmtools.core import EntityStatus
from idmtools.entities import IExperiment, IPlatform
# we have to import brokers so that the proper configuration is achieved for redis
from idmtools_platform_local.client.simulations_client import SimulationsClient
from idmtools_platform_local.local_docker_manager import LocalDockerManager
from idmtools_platform_local.tasks.create_experiement import CreateExperimentTask
from idmtools_platform_local.tasks.create_simulation import CreateSimulationTask
from idmtools_platform_local.tasks.run import RunTask

status_translate = dict(
    created='CREATED',
    in_progress='RUNNING',
    canceled='canceled',
    failed='FAILED',
    done='SUCCEEDED'
)


def local_status_to_common(status):
    return EntityStatus[status_translate[status]]


@dataclass
class LocalPlatform(IPlatform):
    auto_remove: bool = True
    network: str = 'idmtools'
    redis_image: str = 'redis:5.0.4-alpine'
    redis_port: int = 6379
    runtime: Optional[str] = None
    redis_mem_limit: str = '128m'
    redis_mem_reservation: str = '64m'
    postgres_image: str = 'postgres:11.4'
    postgres_mem_limit: str = '64m'
    postgres_mem_reservation: str = '32m'
    postgres_port: Optional[str] = 5432
    workers_image: str = 'idm-docker-production.packages.idmod.org:latest'
    workers_ui_port: int = 5000

    def __post_init__(self):
        # extract configuration details for the docker manager
        local_docker_options = [f.name for f in dataclasses.fields(LocalDockerManager)]
        opts = {k:v for k, v in self.__dict__.items() if k in local_docker_options}
        self.dm = LocalDockerManager(**opts)

    """
    Represents the platform allowing to run simulations locally.
    """

    def retrieve_experiment(self, experiment_id):
        pass

    def get_assets_for_simulation(self, simulation, output_files):
        raise NotImplemented("Not implemented yet in the LocalPlatform")

    def restore_simulations(self, experiment):
        raise NotImplemented("Not implemented yet in the LocalPlatform")

    def refresh_experiment_status(self, experiment: 'TExperiment'):
        """

        Args:
            experiment:

        Returns:

        """
        # TODO Cleanup Client to return experiment id status directly
        status = SimulationsClient.get_all(experiment_id=experiment.uid)
        for s in experiment.simulations:
            sim_status = [st for st in status if st['simulation_uid'] == s.uid]

            if sim_status:
                s.status = local_status_to_common(sim_status[0]['status'])

    def create_experiment(self, experiment: IExperiment):
        m = CreateExperimentTask.send(experiment.tags, experiment.simulation_type)
        eid = m.get_result(block=True)
        experiment.uid = eid
        self.send_assets_for_experiment(experiment)

    def send_assets_for_experiment(self, experiment):
        # Go through all the assets
        for asset in experiment.assets:
            path = os.path.join("/data", experiment.uid, "Assets", asset.filename)
            self.dm.copy_to_container(self.dm.get_workers(), path)

    def send_assets_for_simulation(self, simulation):
        # Go through all the assets
        for asset in simulation.assets:
            path = os.path.join("/data", simulation.experiment.uid, simulation.uid, asset.filename)
            self.dm.copy_to_container(self.dm.get_workers(), path)

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
