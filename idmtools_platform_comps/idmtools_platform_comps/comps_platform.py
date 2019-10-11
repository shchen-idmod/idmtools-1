import json
import logging
import ntpath
import os
import typing
from dataclasses import dataclass, field
from uuid import UUID

from COMPS import Client
from COMPS.Data import AssetCollection as COMPSAssetCollection, AssetCollectionFile, Configuration, Experiment as COMPSExperiment, \
    QueryCriteria, Simulation as COMPSSimulation, SimulationFile, Suite as COMPSSuite

from idmtools.core import CacheEnabled, EntityContainer, ObjectType
from idmtools.core.experiment_factory import experiment_factory
from idmtools.core.interfaces.ientity import IEntity
from idmtools.entities import IPlatform
from idmtools.entities.iexperiment import IExperiment
from idmtools.entities.isimulation import ISimulation
from idmtools.utils.time import timestamp
from idmtools_platform_comps.utils import convert_COMPS_status

if typing.TYPE_CHECKING:
    from typing import NoReturn, List, Dict
    from idmtools.entities.iexperiment import TExperiment
    from idmtools.entities.iitem import TItemList, TItem
    from idmtools.entities.isimulation import TSimulationList, TSimulation

logging.getLogger('COMPS.Data.Simulation').disabled = True
logger = logging.getLogger(__name__)


class COMPSPriority:
    Lowest = "Lowest"
    BelowNormal = "BelowNormal"
    Normal = "Normal"
    AboveNormal = "AboveNormal"
    Highest = "Highest"


@dataclass
class COMPSPlatform(IPlatform, CacheEnabled):
    """
    Represents the platform allowing to run simulations on COMPS.
    """
    MAX_SUBDIRECTORY_LENGTH = 35  # avoid maxpath issues on COMPS

    endpoint: str = field(default="https://comps2.idmod.org")
    environment: str = field(default="Bayesian")
    priority: str = field(default=COMPSPriority.Lowest)
    simulation_root: str = field(default="$COMPS_PATH(USER)\\output")
    node_group: str = field(default="emod_abcd")
    num_retires: int = field(default=0)
    num_cores: int = field(default=1)
    exclusive: bool = field(default=False)

    def __post_init__(self):
        super().__post_init__()
        print("\nUser Login:")
        print(json.dumps({"endpoint": self.endpoint, "environment": self.environment}, indent=3))
        self._login()
        self.supported_types = {ObjectType.EXPERIMENT, ObjectType.SIMULATION, ObjectType.SUITE, ObjectType.ASSETCOLLECTION}

    def _login(self):
        try:
            Client.auth_manager()
        except RuntimeError:
            Client.login(self.endpoint)

    def send_assets(self, item, **kwargs) -> 'NoReturn':
        # TODO: add asset sending for suites if needed
        if isinstance(item, ISimulation):
            self._send_assets_for_simulation(simulation=item, **kwargs)
        elif isinstance(item, IExperiment):
            self._send_assets_for_experiment(experiment=item, **kwargs)
        else:
            raise Exception(f'Unknown how to send assets for item type: {type(item)} '
                            f'for platform: {self.__class__.__name__}')

    @staticmethod
    def _send_assets_for_experiment(experiment: 'TExperiment', **kwargs) -> 'NoReturn':

        if experiment.assets.count == 0:
            return

        ac = COMPSAssetCollection()
        for asset in experiment.assets:
            ac.add_asset(AssetCollectionFile(file_name=asset.filename, relative_path=asset.relative_path),
                         data=asset.content)
        ac.save()
        experiment.assets.uid = ac.id
        print("Asset collection for experiment: {}".format(ac.id))

        # associate the assets with the experiment in COMPS
        e = COMPSExperiment.get(id=experiment.uid)
        e.configuration = Configuration(asset_collection_id=ac.id)
        e.save()

    @staticmethod
    def _send_assets_for_simulation(simulation, comps_simulation) -> 'NoReturn':
        for asset in simulation.assets:
            comps_simulation.add_file(simulationfile=SimulationFile(asset.filename, 'input'), data=asset.content)

    @staticmethod
    def _clean_experiment_name(experiment_name: str) -> str:
        """
        Enforce any COMPS-specific demands on experiment names.
        Args:
            experiment_name: name of the experiment
        Returns: the experiment name allowed for use
        """
        for c in ['/', '\\', ':']:
            experiment_name = experiment_name.replace(c, '_')
        return experiment_name

    def _create_experiment(self, experiment: 'TExperiment') -> 'UUID':
        self._login()

        # Cleanup the name
        experiment_name = COMPSPlatform._clean_experiment_name(experiment.name)

        # Define the subdirectory
        subdirectory = experiment_name[0:self.MAX_SUBDIRECTORY_LENGTH] + '_' + timestamp()

        config = Configuration(
            environment_name=self.environment,
            simulation_input_args=experiment.command.arguments + " " + experiment.command.options,
            working_directory_root=os.path.join(self.simulation_root, subdirectory),
            executable_path=experiment.command.executable,
            node_group_name=self.node_group,
            maximum_number_of_retries=self.num_retires,
            priority=self.priority,
            min_cores=self.num_cores,
            max_cores=self.num_cores,
            exclusive=self.exclusive
        )

        e = COMPSExperiment(name=experiment_name,
                            configuration=config,
                            suite_id=experiment.suite_id)

        # Add tags if present
        if experiment.tags:
            e.set_tags(experiment.tags)

        # Save the experiment
        e.save()

        # Set the ID back in the object
        experiment.uid = e.id

        # Send the assets for the experiment
        self.send_assets(item=experiment)

        return experiment.uid

    def create_items(self, items: 'TItemList') -> 'List[UUID]':
        # TODO: add ability to create suites
        types = list({type(item) for item in items})
        if len(types) != 1:
            raise Exception('create_items only works with items of a single type at a time.')
        sample_item = items[0]
        if isinstance(sample_item, ISimulation):
            ids = self._create_simulations(simulation_batch=items)
        elif isinstance(sample_item, IExperiment):
            ids = [self._create_experiment(experiment=item) for item in items]
        else:
            raise Exception(f'Unable to create items of type: {type(sample_item)} '
                            f'for platform: {self.__class__.__name__}')
        for item in items:
            item.platform = self
        return ids

    def _create_simulations(self, simulation_batch: 'TSimulationList') -> 'List[uuid]':
        self._login()
        created_simulations = []

        for simulation in simulation_batch:
            s = COMPSSimulation(name=simulation.experiment.name, experiment_id=simulation.experiment.uid)
            self.send_assets(item=simulation, comps_simulation=s)
            s.set_tags(simulation.tags)
            created_simulations.append(s)

        COMPSSimulation.save_all(None, save_semaphore=COMPSSimulation.get_save_semaphore())

        # Register the IDs
        return [s.id for s in created_simulations]

    def run_items(self, items: 'TItemList') -> 'NoReturn':
        for item in items:
            if isinstance(item, IExperiment):
                item.get_platform_object().commission()
            else:
                raise Exception("comps_platform.run_items only supports Experiments for now...")

    def _get_object_of_type(self, object_id, object_type, **kwargs):
        # Retrieve the eventual columns/children arguments
        cols = kwargs.get('columns')
        children = kwargs.get('children')

        self._login()

        if object_type == ObjectType.EXPERIMENT:
            cols = cols or ["id", "name"]
            children = children if children is not None else ["tags", "configuration"]
            return COMPSExperiment.get(id=object_id,
                                       query_criteria=QueryCriteria().select(cols).select_children(children))

        if object_type == ObjectType.SIMULATION:
            cols = cols or ["id", "name", "experiment_id", "state"]
            children = children if children is not None else ["tags"]
            return COMPSSimulation.get(id=object_id,
                                       query_criteria=QueryCriteria().select(cols).select_children(children))

        if object_type == ObjectType.ASSETCOLLECTION:
            children = children if children is not None else ["assets"]
            return COMPSAssetCollection.get(id=object_id, query_criteria=QueryCriteria().select_children(children))

    def _create_object(self, platform_object, **kwargs):
        if isinstance(platform_object, COMPSExperiment):
            # Create an experiment
            experiment = experiment_factory.create(platform_object.tags.get("type"), tags=platform_object.tags,
                                                   name=platform_object.name)
            # Set the correct attributes
            experiment.uid = platform_object.id
            experiment.platform = self
            experiment.comps_experiment = platform_object
            return experiment
        elif isinstance(platform_object, COMPSSimulation):
            # Recreate the experiment if needed
            experiment = kwargs.get('experiment') or self.get_object(platform_object.experiment_id, object_type=ObjectType.EXPERIMENT)
            # Get a simulation
            sim = experiment.simulation()
            # Set its correct attributes
            sim.uid = platform_object.id
            sim.tags = platform_object.tags
            sim.status = convert_COMPS_status(platform_object.state)
            return sim

    def get_parent_for_platform_item(self, platform_item, raw=False, **kwargs):
        if isinstance(platform_item, COMPSExperiment):
            # For experiment -> find the suite
            return self.get_object(platform_item.suite_id, object_type=ObjectType.SUITE, raw=raw, **kwargs) if platform_item.suite_id else None
        if isinstance(platform_item, COMPSSimulation):
            # For a simulation, find the experiment
            return self.get_object(platform_item.experiment_id, object_type=ObjectType.EXPERIMENT,
                                  raw=raw, **kwargs) if platform_item.experiment_id else None
        # If Suite return None
        return None

    def get_children_for_platform_item(self, platform_item, raw=False, **kwargs):
        if isinstance(platform_item, COMPSExperiment):
            cols = kwargs.get("cols")
            children = kwargs.get("children")
            cols = cols or ["id", "name", "experiment_id", "state"]
            children = children if children is not None else ["tags"]

            children = platform_item.get_simulations(
                query_criteria=QueryCriteria().select(cols).select_children(children))
            if not raw:
                experiment = self._create_object(platform_item)
                return EntityContainer([self._create_object(s, experiment=experiment) for s in children])
            else:
                return children
        elif isinstance(platform_item, COMPSSuite):
            return EntityContainer([self.get_object(e.id, object_type=ObjectType.EXPERIMENT, raw=raw) for e in
                        COMPSExperiment.get(query_criteria=QueryCriteria().where("suite_id={}".format(platform_item.id)))])

        return None

    def refresh_status(self, item) -> 'NoReturn':
        if isinstance(item, IExperiment):
            simulations = self.get_children(item.uid, ObjectType.EXPERIMENT, force=True, raw=True, cols=["id", "state"], children=[])
            for s in simulations:
                item.simulations.set_status_for_item(s.id, convert_COMPS_status(s.state))

            return

        raise NotImplemented("comps_platform.refresh_status only implemented for Experiments")

    def _get_file_for_collection(self, collection_id: 'UUID', file_path: str) -> 'NoReturn':
        print(f"Cache miss for {collection_id} {file_path}")

        # retrieve the collection
        ac = self.get_object(collection_id, ObjectType.ASSETCOLLECTION, raw=True)

        # Look for the asset file in the collection
        file_name = ntpath.basename(file_path)
        path = ntpath.dirname(file_path).lstrip(f"Assets\\")

        for asset_file in ac.assets:
            if asset_file.file_name == file_name and (asset_file.relative_path or '') == path:
                return asset_file.retrieve()

    def get_files(self, item: 'IEntity', files: 'List[str]') -> 'Dict':
        self._login()

        # Retrieve the simulation from COMPS
        # TODO: revert back to normal object retrieval when pyCOMPS fix 'rollup' configurations.
        # comps_simulation = item.get_platform_object(force=True, cols=['id', 'experiment_id'], children=["files", "configuration"])

        # Temporary stand-in for pycomps fix; code below from Jeff S.
        class QueryCriteriaExt(QueryCriteria):
            _ep_dict = None

            def add_extra_params(self, ep_dict):
                self._ep_dict = ep_dict
                return self

            def to_param_dict(self, ent_type):
                pd = super(QueryCriteriaExt, self).to_param_dict(ent_type)
                if self._ep_dict:
                    pd = {**pd, **self._ep_dict}
                return pd

        comps_simulation = COMPSSimulation.get(item.uid, query_criteria=QueryCriteriaExt().select(
            ['id', 'experiment_id']).select_children(
            ["files", "configuration"]).add_extra_params({'coalesceconfig': True}))

        # Separate the output files in 2 groups:
        # - one for the transient files (retrieved through the comps simulation)
        # - one for the asset collection files (retrieved through the asset collection)
        all_paths = set(files)
        assets = set(path for path in all_paths if path.lower().startswith("assets"))
        transients = all_paths.difference(assets)

        # Create the return dict
        ret = {}

        # Retrieve the transient if any
        if transients:
            transient_files = comps_simulation.retrieve_output_files(paths=transients)
            ret = dict(zip(transients, transient_files))

        # Take care of the assets
        if assets:
            # Get the collection_id for the simulation
            collection_id = comps_simulation.configuration.asset_collection_id

            # Retrieve the files
            for file_path in assets:
                # Normalize the separators
                normalized_path = ntpath.normpath(file_path)
                ret[file_path] = self.cache.memoize()(self._get_file_for_collection)(collection_id, normalized_path)

        return ret
