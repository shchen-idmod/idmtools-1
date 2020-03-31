import os
from dataclasses import dataclass, field
from itertools import tee
from logging import getLogger, DEBUG
from typing import Any, List, Type, Generator, NoReturn
from uuid import UUID

from COMPS.Data import Experiment as COMPSExperiment, QueryCriteria, Configuration, Suite as COMPSSuite
from idmtools.core import ItemType
from idmtools.core.experiment_factory import experiment_factory
from idmtools.entities import CommandLine
from idmtools.entities.experiment import Experiment
from idmtools.entities.iplatform_ops.iplatform_experiment_operations import IPlatformExperimentOperations
from idmtools.entities.templated_simulation import TemplatedSimulations
from idmtools.utils.collections import ParentIterator
from idmtools.utils.time import timestamp
from idmtools_platform_comps.utils.general import clean_experiment_name, convert_comps_status

logger = getLogger(__name__)


@dataclass
class CompsPlatformExperimentOperations(IPlatformExperimentOperations):
    platform: 'COMPSPlaform'  # noqa F821
    platform_type: Type = field(default=COMPSExperiment)

    def get(self, experiment_id: UUID, **kwargs) -> COMPSExperiment:
        cols = kwargs.get('columns')
        children = kwargs.get('children')
        cols = cols or ["id", "name", "suite_id"]
        children = children if children is not None else ["tags", "configuration"]
        return COMPSExperiment.get(id=experiment_id,
                                   query_criteria=QueryCriteria().select(cols).select_children(children))

    def pre_create(self, experiment: Experiment, **kwargs) -> NoReturn:
        if experiment.name is None:
            raise ValueError("Experiment name is required on COMPS")
        super().pre_create(experiment, **kwargs)

    def platform_create(self, experiment: Experiment, num_cores: int = None, executable_path: str = None,
                        command_arg: str = None, priority: str = None) -> COMPSExperiment:
        # TODO check experiment task supported

        # Cleanup the name
        experiment_name = clean_experiment_name(experiment.name)

        # Define the subdirectory
        subdirectory = experiment_name[0:self.platform.MAX_SUBDIRECTORY_LENGTH] + '_' + timestamp()

        exp_command: CommandLine = None
        if isinstance(experiment.simulations, Generator):
            sim_gen1, sim_gen2 = tee(experiment.simulations)
            experiment.simulations = sim_gen2
            exp_command = next(sim_gen1).task.command
        elif isinstance(experiment.simulations, ParentIterator) and isinstance(experiment.simulations.items,
                                                                               TemplatedSimulations):
            exp_command = experiment.simulations.items.base_task.command
            # TODO generators
        else:
            exp_command = experiment.simulations[0].task.command

        if command_arg is None:
            command_arg = exp_command.arguments + " " + exp_command.options

        if executable_path is None:
            executable_path = exp_command.executable
        comps_config = dict(environment_name=self.platform.environment,
                            simulation_input_args=command_arg,
                            working_directory_root=os.path.join(self.platform.simulation_root, subdirectory).replace(
                                '\\', '/'),
                            executable_path=executable_path,
                            node_group_name=self.platform.node_group,
                            maximum_number_of_retries=self.platform.num_retries,
                            priority=self.platform.priority if priority is None else priority,
                            min_cores=self.platform.num_cores if num_cores is None else num_cores,
                            max_cores=self.platform.num_cores if num_cores is None else num_cores,
                            exclusive=self.platform.exclusive
                            )

        if logger.isEnabledFor(DEBUG):
            logger.debug(f'COMPS Experiment Configs: {str(comps_config)}')
        config = Configuration(**comps_config)

        e = COMPSExperiment(name=experiment_name,
                            configuration=config,
                            suite_id=experiment.parent_id)

        # Add tags if present
        if experiment.tags:
            e.set_tags(experiment.tags)

        # Save the experiment
        e.save()

        # Set the ID back in the object
        experiment.uid = e.id

        # Send the assets for the experiment
        self.send_assets(experiment)
        return e

    def post_run_item(self, experiment: Experiment, **kwargs):
        super().post_run_item(experiment, **kwargs)
        print(f'The running experiment can be viewed at {self.platform.endpoint}/#explore/'
              f'Simulations?filters=ExperimentId={experiment.uid}')

    def get_children(self, experiment: COMPSExperiment, **kwargs) -> List[Any]:
        cols = kwargs.get("cols")
        children = kwargs.get("children")
        cols = cols or ["id", "name", "experiment_id", "state"]
        children = children if children is not None else ["tags"]

        children = experiment.get_simulations(query_criteria=QueryCriteria().select(cols).select_children(children))
        return children

    def get_parent(self, experiment: COMPSExperiment, **kwargs) -> Any:
        if experiment.suite_id is None:
            return None
        return self.platform._suites.get(experiment.suite_id, **kwargs)

    def platform_run_item(self, experiment: Experiment, **kwargs):
        if logger.isEnabledFor(DEBUG):
            logger.debug(f'Commissioning experiment: {experiment.uid}')
        experiment.get_platform_object().commission()

    def send_assets(self, experiment: Experiment, **kwargs):
        if experiment.assets.count == 0:
            logger.warning('Experiment has not assets')

        ac = self.platform._assets.create(experiment.assets)
        print("Asset collection for experiment: {}".format(ac.id))

        # associate the assets with the experiment in COMPS
        e = COMPSExperiment.get(id=experiment.uid)
        e.configuration = Configuration(asset_collection_id=ac.id)
        e.save()

    def refresh_status(self, experiment: Experiment, **kwargs):
        simulations = self.get_children(experiment.get_platform_object(), force=True, cols=["id", "state"], children=[])
        for s in simulations:
            experiment.simulations.set_status_for_item(s.id, convert_comps_status(s.state))

    def to_entity(self, experiment: COMPSExperiment, parent: COMPSSuite = None, **kwargs) -> Experiment:
        # Recreate the suite if needed
        if experiment.suite_id is None:
            suite = kwargs.get('suite')
        else:
            if parent:
                suite = parent
            else:
                suite = kwargs.get('suite') or self.platform.get_item(experiment.suite_id, item_type=ItemType.SUITE)

        # Create an experiment
        experiment_type = experiment.tags.get("type") if experiment.tags is not None else ""
        obj = experiment_factory.create(experiment_type, tags=experiment.tags, name=experiment.name,
                                        fallback=Experiment)

        # Convert all simulations
        comps_sims = experiment.get_simulations()
        # from idmtools.entities.iplatform import ITEM_TYPE_TO_OBJECT_INTERFACE
        # interface = ITEM_TYPE_TO_OBJECT_INTERFACE[ItemType.SIMULATION]
        # obj.simulations = [getattr(self.platform, interface).to_entity(s) for s in comps_sims]    # Cause recursive call...

        # Temp workaround
        from idmtools.entities.simulation import Simulation
        from idmtools.core import EntityContainer
        obj.simulations = EntityContainer([Simulation(_uid=s.id, task=None) for s in comps_sims])

        # Set parent
        obj.parent = suite

        # Set the correct attributes
        obj.uid = experiment.id
        obj.comps_experiment = experiment
        return obj