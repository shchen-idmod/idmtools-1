import os
import itertools
import logging
from multiprocessing import cpu_count
from dramatiq import GenericActor

from idmtools_platform_local.internals.workers.utils import get_host_data_bind
from idmtools_platform_local.status import Status
from idmtools_platform_local.internals.tasks.general_task import BaseTask

logger = logging.getLogger(__name__)
cpu_sequence = itertools.cycle(range(0, cpu_count() - 1))


class DockerBaseTask(BaseTask):
    def docker_perform(self, command: str, experiment_uuid: str, simulation_uuid: str, container_config: dict) \
            -> Status:
        from idmtools_platform_local.internals.workers.utils import create_or_update_status
        container_config = container_config
        # update the config to container the volume info

        # Define our simulation path and our root asset path
        simulation_path = os.path.join(os.getenv("DATA_PATH", "/data"), experiment_uuid, simulation_uuid)

        container_config['detach'] = True
        container_config['stderr'] = True
        container_config['working_dir'] = simulation_path
        if os.getenv('CURRENT_UID', None) is not None:
            container_config['user'] = os.getenv('CURRENT_UID')
        container_config['auto_remove'] = True
        # we have to mount using the host data path
        data_dir = get_host_data_bind()
        data_dir += "\\" if "\\" in data_dir else "/"
        container_config['volumes'] = {
            data_dir: dict(bind='/data', mode='rw'),
        }
        # limit cpu_workers
        if cpu_count() > 2:

            container_config['cpuset_cpus'] = f'{next(cpu_sequence)}'

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Task Docker Config: {str(container_config)}")

        current_job = self.get_current_job(experiment_uuid, simulation_uuid, command)
        if self.is_canceled(current_job):
            return current_job.status

        result = self.run_container(command, container_config, current_job, simulation_path, simulation_uuid)
        # check if we succeeded
        if result:
            logger.info(result['StatusCode'])
            return_code = result['StatusCode']
        else:
            return_code = -999
        status = self.extract_status(experiment_uuid, return_code, simulation_uuid)
        # Update task with the final status
        create_or_update_status(simulation_uuid, status=status, extra_details=current_job.extra_details)
        return status

    def run_container(self, command, container_config, current_job, simulation_path, simulation_uuid):
        import docker
        from idmtools_platform_local.internals.workers.utils import create_or_update_status
        result = None
        with open(os.path.join(simulation_path, "StdOut.txt"), "w") as out, \
                open(os.path.join(simulation_path, "StdErr.txt"), "w") as err:  # noqa: F841
            try:
                client = docker.DockerClient(base_url='unix://var/run/docker.sock')
                dcmd = f'docker run -v {get_host_data_bind()}:/data --user \"{os.getenv("CURRENT_UID")}\" ' \
                    f'-w {container_config["working_dir"]} {container_config["image"]} {command}'
                logger.info(f"Running docker command: {dcmd}")
                logger.info(f"Running {command} with docker config {str(container_config)}")
                out.write(f"{command}\n")

                container = client.containers.run(command=command, **container_config)
                log_reader = container.logs(stream=True)

                current_job.extra_details['container_id'] = container.id
                # Log that we have started this particular simulation
                create_or_update_status(simulation_uuid, status=Status.in_progress, extra_details=current_job.extra_details)
                for output in log_reader:
                    out.write(output.decode("utf-8"))
                result = container.wait()
            except Exception as e:
                err.write(str(e))
                raise e
        return result


class DockerRunTask(GenericActor, DockerBaseTask):
    class Meta:
        store_results = False
        max_retries = 0
        queue_name = "cpu"

    def perform(self, command: str, experiment_uuid: str, simulation_uuid: str, container_config: dict) -> Status:
        return self.docker_perform(command, experiment_uuid, simulation_uuid, container_config)


# it would be great we could just derive from RunTask and change the meta but that doesn't seem to work with
# GenericActors for some reason. Using BaseTask and these few lines of redundant code are our compromise
class GPURunTask(GenericActor, DockerBaseTask):
    class Meta:
        store_results = False
        max_retries = 0
        queue_name = "gpu"

    def perform(self, command: str, experiment_uuid: str, simulation_uuid: str, container_config: dict) -> Status:
        return self.docker_perform(command, experiment_uuid, simulation_uuid, container_config)