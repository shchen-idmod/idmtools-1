import typing

from idmtools.services.experiments import ExperimentPersistService
from idmtools.core import ExperimentNotFound
from idmtools.services.platforms import PlatformPersistService

if typing.TYPE_CHECKING:
    from idmtools.core import TPlatform, TExperiment
    import uuid


def retrieve_experiment(experiment_id: 'uuid', platform: 'TPlatform' = None,
                        with_simulations: 'bool' = False) -> 'TExperiment':
    experiment = ExperimentPersistService.retrieve(experiment_id)
    if not experiment:
        # This is an unknown experiment, make sure we have a platform to ask for info
        if not platform:
            raise ExperimentNotFound(experiment_id)

        # Try to retrieve it from the platform
        experiment = platform.retrieve_experiment(experiment_id)
        if not experiment:
            raise ExperimentNotFound(experiment_id, platform)

        # We have the experiment -> persist it for next time
        experiment.platform_id = PlatformPersistService.save(platform)
        ExperimentPersistService.save(experiment)

    # At this point we have our experiment -> check if we need the simulations
    if with_simulations:
        platform.restore_simulations(experiment)

    return experiment
