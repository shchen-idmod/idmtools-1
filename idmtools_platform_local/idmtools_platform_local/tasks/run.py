import itertools
import logging
import os
import shlex
import sys
import subprocess
from multiprocessing import cpu_count

from dramatiq import GenericActor
from idmtools_platform_local.status import Status

logger = logging.getLogger(__name__)
cpu_sequence = itertools.cycle(range(0, cpu_count()-1))


class BaseTask:
    @staticmethod
    def run_task(command: str, current_job: 'JobStatus', experiment_uuid: str, simulation_path: str,
                 simulation_uuid: str) -> Status:
        """
        Executes the command and record its status in the database

        Args:
            command: command to run
            current_job: The JobStatus object to update
            experiment_uuid: experiment id
            simulation_path: Base root of the simulation execution path
            simulation_uuid: Simulation Id

        Returns:
            (Status) Status of the job. This is determine by the system return code of the process
        """
        from idmtools_platform_local.workers.utils import create_or_update_status
        # Open of Stdout and StdErr files that will be used to track input and output
        logger.debug(f"Simulation path {simulation_path}")
        with open(os.path.join(simulation_path, "StdOut.txt"), "w") as out, \
                open(os.path.join(simulation_path, "StdErr.txt"), "w") as err:
            logger.info('Executing %s from working directory %s', command, simulation_path)
            err.write(f"{command}\n")

            # Run our task
            p = subprocess.Popen(shlex.split(command), cwd=simulation_path, shell=False, stdout=out, stderr=err)
            # store the pid in case we want to cancel later
            logger.info(f"Process id: {p.pid}")
            current_job.extra_details['pid'] = p.pid
            # Log that we have started this particular simulation
            create_or_update_status(simulation_uuid, status=Status.in_progress, extra_details=current_job.extra_details)
            p.wait()

            status = RunTask.extract_status(experiment_uuid, p.returncode, simulation_uuid)

            # Update task with the final status
            create_or_update_status(simulation_uuid, status=status, extra_details=current_job.extra_details)
            return status

    @staticmethod
    def extract_status(experiment_uuid: str, return_code: int, simulation_uuid) -> Status:
        """
        Extract status from a completed process
        Args:
            experiment_uuid: Id of experiment(needed to update job info)
            process: Process that has finished execution
            simulation_uuid: Simulation id of the task

        Returns:
            (Status) Status of the job
        """
        from idmtools_platform_local.workers.data.job_status import JobStatus
        from idmtools_platform_local.workers.database import get_session
        # Determine if the task succeeded or failed
        status = Status.done if return_code == 0 else Status.failed
        # If it failed, we should let the user know with a log message
        if status == Status.failed:
            # it is possible we killed the process through canceling. Let's check to be sure
            # before marking as canceled
            current_job: JobStatus = get_session().query(JobStatus). \
                filter(JobStatus.uuid == simulation_uuid, JobStatus.parent_uuid == experiment_uuid).first()
            if current_job.status == Status.canceled:
                status = Status.canceled
            logger.error('Simulation %s for Experiment %s failed with a return code of %s',
                         simulation_uuid, experiment_uuid, return_code)
        elif logger.isEnabledFor(logging.DEBUG):
            logging.debug('Simulation %s finished with status of %s', simulation_uuid, str(status))
        return status

    def get_current_job(self, experiment_uuid, simulation_uuid, command):
        from idmtools_platform_local.workers.data.job_status import JobStatus
        from idmtools_platform_local.workers.database import get_session
        # Get the current job
        current_job: JobStatus = get_session().query(JobStatus). \
            filter(JobStatus.uuid == simulation_uuid, JobStatus.parent_uuid == experiment_uuid).first()
        current_job.extra_details['command'] = command
        return current_job

    def is_canceled(self, current_job):
        from idmtools_platform_local.workers.utils import create_or_update_status
        if current_job.status == Status.canceled:
            logger.info(f'Job {current_job.uuid} has been canceled')
            # update command extra_details. Useful in future for deletion
            create_or_update_status(current_job.uuid, extra_details=current_job.extra_details)
            return True
        return False

    def execute_simulation(self, command, experiment_uuid, simulation_uuid):
        """
            Runs our task and updates status

            Args:
                command: Command string to execute
                experiment_uuid: Experiment id of task
                simulation_uuid: Simulation id of task

            Returns:

            """
        # we only want to import this here so that clients don't need postgres/sqlalchemy packages
        current_job = self.get_current_job(experiment_uuid, simulation_uuid, command)
        if self.is_canceled(current_job):
            return current_job.status
        # Define our simulation path and our root asset path
        simulation_path = os.path.join(os.getenv("DATA_PATH", "/data"), experiment_uuid, simulation_uuid)
        asset_dir = os.path.join(simulation_path, "Assets")
        # Add items to our system path
        sys.path.insert(0, simulation_path)
        sys.path.insert(0, asset_dir)
        # add to our details so it can be used for traceability downstream
        current_job.extra_details['system_path'] = sys.path
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'System path: {sys.path}')
        return self.run_task(command, current_job, experiment_uuid, simulation_path, simulation_uuid)


class DockerBaseTask(BaseTask):
    def docker_perform(self, command: str, experiment_uuid: str, simulation_uuid: str, container_config: dict)-> Status:
        from idmtools_platform_local.workers.utils import create_or_update_status
        container_config = container_config
        # update the config to container the volume info

        # Define our simulation path and our root asset path
        simulation_path = os.path.join(os.getenv("DATA_PATH", "/data"), experiment_uuid, simulation_uuid)
        asset_dir = os.path.join(simulation_path, "Assets")

        container_config['detach'] = True
        container_config['stderr'] = True
        container_config['working_dir'] = simulation_path
        container_config['user'] = os.getenv('CURRENT_UID')
        # container_config['auto_remove'] = True
        # we have to mount using the host data path
        data_dir = f'{os.getenv("HOST_DATA_PATH")}/'
        container_config['volumes'] = {
            data_dir: dict(bind='/data', mode='rw'),
        }
        # limit cpu
        if cpu_count() > 2:

            container_config['cpuset_cpus'] = f'{next(cpu_sequence)}'

        logger.info(f"Task Docker Config: {str(container_config)}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Task Docker Config: {str(container_config)}")

        current_job = self.get_current_job(experiment_uuid, simulation_uuid, command)
        if self.is_canceled(current_job):
            return current_job.status

        result = self.run_container(command, container_config, current_job, simulation_path, simulation_uuid)
        logger.info(result['StatusCode'])
        return_code = result['StatusCode']
        status = self.extract_status(experiment_uuid, return_code, simulation_uuid)
        # Update task with the final status
        create_or_update_status(simulation_uuid, status=status, extra_details=current_job.extra_details)
        return status

    def run_container(self, command, container_config, current_job, simulation_path, simulation_uuid):
        import docker
        from idmtools_platform_local.workers.utils import create_or_update_status
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        with open(os.path.join(simulation_path, "StdOut.txt"), "w") as out, \
                open(os.path.join(simulation_path, "StdErr.txt"), "w") as err:
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
        return result


class RunTask(GenericActor, DockerBaseTask):
    """
    Run the given `command` in the simulation folder.
    """

    class Meta:
        store_results = False
        max_retries = 0
        queue_name = "cpu"

    def perform(self, command: str, experiment_uuid: str, simulation_uuid: str) -> Status:
        return self.execute_simulation(command, experiment_uuid, simulation_uuid)


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

    def perform(self, command: str, experiment_uuid: str, simulation_uuid: str,  container_config: dict) -> Status:
        return self.docker_perform(command, experiment_uuid, simulation_uuid, container_config)

