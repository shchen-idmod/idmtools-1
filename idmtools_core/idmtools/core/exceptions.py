import typing
from uuid import UUID

if typing.TYPE_CHECKING:
    from idmtools.entities.iplatform import TPlatform


class ExperimentNotFound(Exception):
    def __init__(self, experiment_id: UUID, platform: 'TPlatform' = None):
        if platform:
            super().__init__(f"Experiment with id '{experiment_id}' could not be retrieved on platform {platform}.")
        else:
            super().__init__(f"Experiment with id '{experiment_id}' could not be retrieved.")


class UnknownItemException(Exception):
    def __init__(self, err: 'str'):
        super().__init__(err)
