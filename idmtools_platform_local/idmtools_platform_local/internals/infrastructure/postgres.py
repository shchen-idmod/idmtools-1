from dataclasses import dataclass
from logging import getLogger, DEBUG
from typing import Dict, NoReturn

from docker.models.containers import Container

from idmtools_platform_local.internals.infrastructure.base_docker import BaseServiceContainer

logger = getLogger(__name__)


@dataclass
class PostgresContainer(BaseServiceContainer):
    host_data_directory: str = None
    port: int = 5432
    mem_limit: str = '128m'
    mem_reservation: str = '32m'
    run_as: str = None
    image: str = 'postgres:11.4'
    container_name: str = 'idmtools_postgres'
    # TODO Make this secure by loading from keyring or encrypted file and then pass through docker screts
    password: str = 'idmtools'
    data_volume_name: str = 'idmtools_local_postgres'
    config_prefix: str = 'postgres_'

    def get_configuration(self) -> Dict:
        """
        Returns the docker config for the postgres container

        Returns:
            (dict) Dictionary representing the docker config for the postgres container
        """
        postgres_volumes = {
            self.data_volume_name: dict(bind='/var/lib/postgresql/data', mode='rw')
        }

        port_bindings = self._get_optional_port_bindings(self.port, 5432)
        container_config = self.get_common_config(container_name=self.container_name, image=self.image,
                                                  port_bindings=port_bindings,
                                                  volumes=postgres_volumes, mem_limit=self.mem_limit,
                                                  network=self.network,
                                                  mem_reservation=self.mem_reservation,
                                                  environment=['POSTGRES_USER=idmtools',
                                                               f'POSTGRES_PASSWORD={self.password}'])
        if logger.isEnabledFor(DEBUG):
            logger.debug(f"Postgres Config: {container_config}")
        return container_config

    def create(self, spinner=None) -> Container:
        self.create_postgres_volume()
        return super().create(spinner)

    def create_postgres_volume(self) -> NoReturn:
        """
        Creates our postgres volume
        Returns:

        """
        postgres_volume = self.client.volumes.list(filters=dict(name=self.data_volume_name))
        if not postgres_volume:
            self.client.volumes.create(name=self.data_volume_name)
