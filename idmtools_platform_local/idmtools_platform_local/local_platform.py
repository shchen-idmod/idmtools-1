import functools
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from logging import getLogger
from typing import Dict, List, NoReturn, Optional, Type
from uuid import UUID

import docker
from docker.models.containers import Container
from math import floor

from idmtools.assets import Asset
from idmtools.core import ItemType
from idmtools.core.experiment_factory import experiment_factory
from idmtools.core.interfaces.ientity import TEntityList
from idmtools.core.interfaces.iitem import TItem, TItemList
from idmtools.core.system_information import get_data_directory
from idmtools.entities import IExperiment, IPlatform
from idmtools.entities.iexperiment import IGPUExperiment, IDockerExperiment, IWindowsExperiment, IDockerGPUExperiment, \
    IHostBinaryExperiment
from idmtools.entities.isimulation import ISimulation, TSimulation
from idmtools.utils.entities import get_dataclass_common_fields
from idmtools_platform_local.client.experiments_client import ExperimentsClient
from idmtools_platform_local.client.simulations_client import SimulationsClient
from idmtools_platform_local.internals.docker_io import DockerIO
from idmtools_platform_local.internals.infrastructure.service_manager import DockerServiceManager

status_translate = dict(
    created='CREATED',
    in_progress='RUNNING',
    canceled='canceled',
    failed='FAILED',
    done='SUCCEEDED'
)


def local_status_to_common(status):
    from idmtools.core import EntityStatus
    return EntityStatus[status_translate[status]]


logger = getLogger(__name__)


@dataclass
class LocalPlatform(IPlatform):
    """
    Represents the platform allowing to run simulations locally.
    """

    host_data_directory: str = field(default=get_data_directory())
    network: str = field(default='idmtools')
    redis_image: str = field(default='redis:5.0.4-alpine')
    redis_port: int = field(default=6379)
    runtime: Optional[str] = field(default=None)
    redis_mem_limit: str = field(default='128m')
    redis_mem_reservation: str = field(default='64m')
    postgres_image: str = field(default='postgres:11.4')
    postgres_mem_limit: str = field(default='64m')
    postgres_mem_reservation: str = field(default='32m')
    postgres_port: Optional[str] = field(default=5432)
    workers_mem_limit: str = field(default='16g')
    workers_mem_reservation: str = field(default='128m')
    workers_image: str = field(default=None)
    workers_ui_port: int = field(default=5000)
    heartbeat_timeout: int = field(default=15)
    default_timeout: int = field(default=45)
    launch_created_experiments_in_browser: bool = field(default=False)
    # allows user to specify auto removal of docker worker containers
    auto_remove_worker_containers: bool = field(default=True)

    # We use this to manage our docker containers
    _do: Optional[DockerIO] = field(default=None, compare=False, metadata={"pickle_ignore": True})
    _sm: Optional[DockerServiceManager] = field(default=None, compare=False, metadata={"pickle_ignore": True})

    def __post_init__(self):
        logger.debug("Setting up local platform")
        self.supported_types = {ItemType.EXPERIMENT, ItemType.SIMULATION}

        # Configure our docker IO client
        if self._do is None:
            # extract configuration details for the docker manager
            opts = get_dataclass_common_fields(self, DockerIO)
            self._do = DockerIO(**opts)

        # Start our docker services
        if self._sm is None:
            client = docker.from_env()
            opts = get_dataclass_common_fields(self, DockerServiceManager)
            self._sm = DockerServiceManager(client, **opts)
            self._sm.create_services()

        super().__post_init__()

    def cleanup(self, delete_data: bool = False, shallow_delete: bool = False, tear_down_brokers: bool = False):
        self._sm.cleanup(delete_data, tear_down_brokers=tear_down_brokers)
        self._do.cleanup(delete_data, shallow_delete=shallow_delete)

    def get_platform_item(self, item_id, item_type, **kwargs):
        if item_type == ItemType.EXPERIMENT:
            experiment_dict = ExperimentsClient.get_one(item_id)
            experiment = experiment_factory.create(experiment_dict['tags'].get("type"), tags=experiment_dict['tags'])
            experiment.uid = experiment_dict['experiment_id']
            return experiment
        elif item_type == ItemType.SIMULATION:
            simulation_dict = SimulationsClient.get_one(item_id)
            experiment = self.get_platform_item(simulation_dict["experiment_id"], ItemType.EXPERIMENT)
            simulation = experiment.simulation()
            simulation.uid = simulation_dict['simulation_uid']
            simulation.tags = simulation_dict['tags']
            simulation.status = local_status_to_common(simulation_dict['status'])
            return simulation

    def get_children_for_platform_item(self, platform_item, raw, **kwargs):
        if isinstance(platform_item, IExperiment):
            platform_item.simulations.clear()

            # Retrieve the simulations for the current page
            simulation_dict = SimulationsClient.get_all(experiment_id=platform_item.uid, per_page=9999)

            # Add the simulations
            for sim_info in simulation_dict:
                sim = platform_item.simulation()
                sim.uid = sim_info['simulation_uid']
                sim.tags = sim_info['tags']
                sim.status = local_status_to_common(sim_info['status'])
                platform_item.simulations.append(sim)

            return platform_item.simulations

    def get_parent_for_platform_item(self, platform_item, raw, **kwargs):
        if isinstance(platform_item, ISimulation):
            return self.get_platform_item(platform_item.parent_id, ItemType.EXPERIMENT)
        return None

    def _create_batch(self, batch: TEntityList, item_type: ItemType) -> 'List[UUID]':  # noqa: F821
        if item_type == ItemType.SIMULATION:
            ids = self._create_simulations(simulations_batch=batch)
        elif item_type == ItemType.EXPERIMENT:
            ids = [self._create_experiment(experiment=item) for item in batch]

        return ids

    def run_items(self, items: TItemList) -> NoReturn:
        from idmtools_platform_local.internals.tasks.general_task import RunTask
        for item in items:
            if item.item_type == ItemType.EXPERIMENT:
                if not self.is_supported_experiment(item):
                    raise ValueError("This experiment type is not support on the LocalPlatform.")
                is_docker_type = isinstance(item, IDockerExperiment)
                for simulation in item.simulations:
                    # if the task is docker, build the extra config
                    if is_docker_type:
                        self.run_docker_sim(item, simulation)
                    else:
                        logger.debug(f"Running simulation: {simulation.uid}")
                        RunTask.send(item.command.cmd, item.uid, simulation.uid)
            else:
                raise Exception(f'Unable to run item id: {item.uid} of type: {type(item)} ')

    def run_docker_sim(self, item, simulation):
        from idmtools_platform_local.internals.tasks.docker_run import DockerRunTask, GPURunTask
        logger.debug(f"Preparing Docker Task Configuration for {item.uid}:{simulation.uid}")
        is_gpu = isinstance(item, IGPUExperiment)
        run_cmd = GPURunTask if is_gpu else DockerRunTask
        docker_config = dict(
            image=item.image_name,
            auto_remove=self.auto_remove_worker_containers
        )
        # if we are running gpu, use nvidia runtime
        if is_gpu:
            docker_config['runtime'] = 'nvidia'
        run_cmd.send(item.command.cmd, item.uid, simulation.uid, docker_config)

    def send_assets(self, item: TItem, **kwargs) -> NoReturn:
        """
        Send assets for item to platform
        """
        if isinstance(item, ISimulation):
            self._send_assets_for_simulation(item, **kwargs)
        elif isinstance(item, IExperiment):
            self._send_assets_for_experiment(item, **kwargs)
        else:
            raise Exception(f'Unknown how to send assets for item type: {type(item)} '
                            f'for platform: {self.__class__.__name__}')

    def refresh_status(self, item) -> NoReturn:
        """
        Refresh the status of the specified item

        """
        if isinstance(item, ISimulation):
            raise Exception(f'Unknown how to refresh items of type {type(item)} '
                            f'for platform: {self.__class__.__name__}')
        elif isinstance(item, IExperiment):
            status = SimulationsClient.get_all(experiment_id=item.uid, per_page=9999)
            for s in item.simulations:
                sim_status = [st for st in status if st['simulation_uid'] == s.uid]

                if sim_status:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"Simulation {sim_status[0]['simulation_uid']}status: {sim_status[0]['status']}")
                    s.status = local_status_to_common(sim_status[0]['status'])

    def get_files(self, item: TItem, files: List[str]) -> Dict[str, bytearray]:
        if not isinstance(item, ISimulation):
            raise NotImplementedError("Retrieving files only implemented for Simulations at the moment")

        return self._get_assets_for_simulation(item, files)

    def _get_assets_for_simulation(self, simulation: TSimulation, output_files) -> Dict[str, bytearray]:  # noqa: F821
        """
        Get assets for a specific simulation

        Args:
            simulation: Simulation object to fetch files for
            output_files: List of files to fetch

        Returns:
            Returns a dict containing mapping of filename->bytearry
        """
        all_paths = set(output_files)

        assets = set(path for path in all_paths if path.lower().startswith("assets"))
        transients = all_paths.difference(assets)

        # Create the return dict
        ret = {}

        # Retrieve the transient if any
        if transients:
            sim_path = f'{simulation.parent_id}/{simulation.uid}'
            transients_files = self.retrieve_output_files(job_id_path=sim_path, paths=transients)
            ret = dict(zip(transients, transients_files))

        # Take care of the assets
        if assets:
            asset_path = f'{simulation.parent_id}'
            common_files = self.retrieve_output_files(job_id_path=asset_path, paths=assets)
            ret.update(dict(zip(assets, common_files)))

        return ret

    def _create_experiment(self, experiment: IExperiment):
        """
        Creates the experiment object on the LocalPlatform
        Args:
            experiment: Experiment object to create

        Returns:
            Id
        """
        from idmtools_platform_local.internals.tasks.create_experiment import CreateExperimentTask
        from dramatiq.results import ResultTimeout
        if not self.is_supported_experiment(experiment):
            raise ValueError("This experiment type is not support on the LocalPlatform.")

        m = CreateExperimentTask.send(experiment.tags, experiment.simulation_type)

        # Create experiment is vulnerable to disconnects early on of redis errors. Lets do a retry on conditions
        start = time.time()
        timeout_diff = 0
        time_increment = self.heartbeat_timeout if self.heartbeat_timeout < self.default_timeout else self.default_timeout
        while self.default_timeout - timeout_diff > 0:
            try:
                eid = m.get_result(block=True, timeout=time_increment * 1000)
                break
            except ResultTimeout as e:
                logger.debug('Resetting broker client because of a heartbeat failure')
                timeout_diff = floor(time.time() - start)
                self._sm.restart_brokers(self.heartbeat_timeout)
                if timeout_diff >= self.default_timeout:
                    logger.exception(e)
                    logger.error("Could not connect to redis")
                    raise e
        experiment.uid = eid
        path = "/".join(["/data", experiment.uid, "Assets"])
        self._do.create_directory(path)
        self._send_assets_for_experiment(experiment)
        if self.launch_created_experiments_in_browser:
            self.launch_item_in_browser(experiment)
        return experiment.uid

    def launch_item_in_browser(self, item):
        if isinstance(item, IExperiment):
            t_str = item.uid
        elif isinstance(item, ISimulation):
            t_str = f'{item.parent_id}/{item.uid}'
        else:
            raise NotImplementedError("Only launching experiments and simulations is supported")
        try:
            import webbrowser
            from idmtools_platform_local.config import get_api_path
            webbrowser.open(f'{get_api_path().replace("/api", "/data")}/{t_str}?sort_by=modified&order=desc')
        except Exception:
            pass

    def _send_assets_for_experiment(self, experiment):
        """
        Sends assets for specified experiment

        Args:
            experiment: Experiment to send assets for

        Returns:
            None
        """
        # Go through all the assets
        path = "/".join(["/data", experiment.uid, "Assets"])
        worker = self._sm.get('workers')
        list(map(functools.partial(self.send_asset_to_docker, path=path, worker=worker), experiment.assets))

    def _send_assets_for_simulation(self, simulation, worker: Container = None):
        """
        Send assets for specified simulation

        Args:
            simulation: Simulation Id
            worker: Options worker container. Useful in batches to reduce overhead

        Returns:
            None
        """
        # Go through all the assets
        path = "/".join(["/data", simulation.experiment.uid, simulation.uid])
        if worker is None:
            worker = self._sm.get('workers')

        items = self.assets_to_copy_multiple_list(path, simulation.assests)
        self._do.copy_multiple_to_container(worker, items)

    def assets_to_copy_multiple_list(self, path, assets):
        """
        Batch copies a set of items assets to a grouped by path
        Args:
            path: Target path
            assets: Assets to copy

        Returns:
            Dict of items groups be path.
        """
        items = defaultdict(list)
        for asset in assets:
            file_path = asset.absolute_path
            remote_path = "/".join([path, asset.relative_path]) if asset.relative_path else path
            self._do.create_directory(remote_path)
            opts = dict(dest_name=asset.filename if asset.filename else file_path)
            if file_path:
                opts['file'] = file_path
            else:
                opts['content'] = asset.content
            items[remote_path].append(opts)
        return items

    def send_asset_to_docker(self, asset: Asset, path: str, worker: Container = None) -> NoReturn:
        """
        Handles sending an asset to docker.

        Args:
            asset: Asset object to send
            path: Path to send find to within docker container
            worker: Optional worker to reduce docker calls

        Returns:
            (NoReturn): Nada
        """
        file_path = asset.absolute_path
        remote_path = "/".join([path, asset.relative_path]) if asset.relative_path else path
        # ensure remote directory exists
        result = self._do.create_directory(remote_path)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Creating directory {remote_path} result: {str(result)}")
        # is it a real file?
        if worker is None:
            worker = self._sm.get('workers')
        src = dict()
        if file_path:
            src['file'] = file_path
        else:
            src['content'] = asset.content
        self._do.copy_to_container(worker, remote_path, dest_name=asset.filename if asset.filename else file_path,
                                   **src)

    def _create_simulations(self, simulations_batch: List[ISimulation]):
        """
        Create a set of simulations

        Args:
            simulations_batch: List of simulations to create

        Returns:
            Ids of simulations created
        """
        from idmtools_platform_local.internals.tasks.create_simulation import CreateSimulationsTask
        worker = self._sm.get('workers')

        m = CreateSimulationsTask.send(simulations_batch[0].experiment.uid, [s.tags for s in simulations_batch])
        ids = m.get_result(block=True, timeout=self.default_timeout * 1000)

        items = dict()
        # update our uids and then build a list of files to copy
        for i, simulation in enumerate(simulations_batch):
            simulation.uid = ids[i]
            path = "/".join(["/data", simulation.experiment.uid, simulation.uid])
            items.update(self.assets_to_copy_multiple_list(path, simulation.assets))
        result = self._do.copy_multiple_to_container(worker, items)
        if not result:
            raise IOError("Coping of data for simulations failed.")
        return ids

    def retrieve_output_files(self, job_id_path, paths):
        """
        Retrieves output files
        Args:
            job_id_path: For experiments, this should just be the id. For simulations, the path should be
            experiment_id/simulation id
            paths:

        Returns:

        """

        byte_arrs = []

        for path in paths:
            full_path = os.path.join(self.host_data_directory, 'workers', job_id_path, path)
            full_path = full_path.replace('\\', os.sep).replace('/', os.sep)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Retrieving file from {full_path}")
            with open(full_path, 'rb') as fin:
                byte_arrs.append(fin.read())
        return byte_arrs

    def supported_experiment_types(self) -> List[Type]:
        return [IExperiment, IDockerExperiment, IDockerGPUExperiment]

    def unsupported_experiment_types(self) -> List[Type]:
        return [IWindowsExperiment, IHostBinaryExperiment]
