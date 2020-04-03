import os
from logging import getLogger, DEBUG
import hashlib
from dataclasses import dataclass, field
from idmtools.assets import Asset
from idmtools.core.interfaces.iitem import IItem
from COMPS.Data.AssetCollection import AssetCollection as COMPSAssetCollection
from COMPS.Data import QueryCriteria
from idmtools.entities.experiment import Experiment
from idmtools.entities.iplatform import IPlatform
from idmtools_models.python.json_python_task import JSONConfiguredPythonTask

CURRENT_DIRECTORY = os.path.dirname(__file__)
REQUIREMENT_FILE = 'requirements_updated.txt'
MODEL_LOAD_LIB = "install_requirements.py"
MODEL_CREATE_AC = 'create_asset_collection.py'
MD5_KEY = 'idmtools-requirements-md5'

logger = getLogger(__name__)


@dataclass(repr=False)
class RequirementsToAssetCollection:
    platform: IPlatform = field(default=None)
    requirements_path: str = field(default=None)
    pkg_list: list = field(default=None)
    local_wheels: list = field(default=None)
    _checksum: str = field(default=None, init=False)
    _requirements: str = field(default=None, init=False)

    def __post_init__(self):
        if not any([self.requirements_path, self.pkg_list, self.local_wheels]):
            raise ValueError(
                "Impossible to proceed without either requirements path or with package list or local wheels!")

        self.requirements_path = os.path.abspath(self.requirements_path) if self.requirements_path else None
        self.pkg_list = self.pkg_list or []
        self.local_wheels = [os.path.abspath(whl) for whl in self.local_wheels] if self.local_wheels else []

    @property
    def checksum(self):
        """
        Returns:
            The md5 of the requirements.
        """
        if not self._checksum:
            req_content = '\n'.join(self.requirements)
            self._checksum = hashlib.md5(req_content.encode('utf-8')).hexdigest()

        return self._checksum

    @property
    def requirements(self):
        """
        Returns:
            Consolidated requirements.
        """
        if not self._requirements:
            self._requirements = self.consolidate_requirements()

        return self._requirements

    def run(self, rerun=False):
        """
        The working logic of this utility:
            1. check if asset collection exists for given requirements, return ac id if exists
            2. create an Experiment to install the requirements on COMPS
            3. create a WorkItem to create a Asset Collection

        Returns: return ac id based on the requirements if Experiment and WorkItem Succeeded
        """
        # Check if ac with md5 exists
        ac = self.retrieve_ac_by_tag()

        if ac and not rerun:
            return ac.id

        # Create Experiment to install custom requirements
        exp = self.run_experiment_to_install_lib()
        if exp is None:
            if logger.isEnabledFor(DEBUG):
                logger.debug('Failed to install requirements!')
            raise Exception('Failed to install requirements!')

        if logger.isEnabledFor(DEBUG):
            logger.debug(f'\nexp: {exp.uid}')

        # Create a WorkItem to create asset collection
        wi = self.run_wi_to_create_ac(exp.uid)
        if wi is None:
            if logger.isEnabledFor(DEBUG):
                logger.debug(f'Failed to create asset collection from experiment: {exp.uid}')
            raise Exception(f'Failed to create asset collection from experiment: {exp.uid}')

        if logger.isEnabledFor(DEBUG):
            logger.debug(f'\nwi: {wi.uid}')

        # get ac or return ad_id
        ac = self.retrieve_ac_by_tag()

        if ac:
            return ac.id

    def save_updated_requirements(self):
        """
        Save consolidated requirements to a file requirements_updated.txt
        Returns:

        """
        req_content = '\n'.join(self.requirements)
        with open(REQUIREMENT_FILE, 'w') as outfile:
            outfile.write(req_content)

    def retrieve_ac_by_tag(self, md5_check=None):
        """
        Retrieve comps asset collection given ac tag
        Args:
            md5_check: also can use custom md5 string as search tag
        Returns: comps asset collection
        """
        md5_str = md5_check or self.checksum
        if logger.isEnabledFor(DEBUG):
            logger.debug(f'md5_str: {md5_str}')

        # check if ac with tag idmtools-requirements-md5 = my_md5 exists
        ac_list = COMPSAssetCollection.get(
            query_criteria=QueryCriteria().select_children('tags').where_tag([f'{MD5_KEY}={md5_str}']))

        # if exists, get ac and return it
        if len(ac_list) > 0:
            ac_list = sorted(ac_list, key=lambda t: t.date_created, reverse=True)
            ac = ac_list[0]
            return ac

    def add_wheels_to_assets(self, experiment):
        for whl in self.local_wheels:
            a = Asset(filename=os.path.basename(whl), absolute_path=whl)
            experiment.add_asset(a)

    def run_experiment_to_install_lib(self):
        """
        Create an Experiment which will run another py script to install requirements
        Returns: Experiment created
        """
        self.save_updated_requirements()

        exp_name = "install custom requirements"
        task = JSONConfiguredPythonTask(script_path=os.path.join(CURRENT_DIRECTORY, MODEL_LOAD_LIB))
        experiment = Experiment(name=exp_name, simulations=[task.to_simulation()])
        experiment.add_asset(Asset(REQUIREMENT_FILE))
        experiment.tags = {MD5_KEY: self.checksum}
        self.add_wheels_to_assets(experiment)

        self.platform.run_items(experiment)
        self.wait_till_done(experiment)

        if experiment.succeeded:
            return experiment

    def run_wi_to_create_ac(self, exp_id):
        """
        Create an WorkItem which will run another py script to create new asset collection
        Args:
            exp_id: the Experiment id (which installed requirements)
        Returns: work item created
        """
        from idmtools.assets.file_list import FileList
        from idmtools_platform_comps.ssmt_work_items.comps_workitems import SSMTWorkItem

        md5_str = self.checksum
        if logger.isEnabledFor(DEBUG):
            logger.debug(f'md5_str: {md5_str}')

        wi_name = "wi to create ac"
        command = f"python {MODEL_CREATE_AC} {exp_id} {md5_str} {self.platform.endpoint}"
        user_files = FileList(root=CURRENT_DIRECTORY, files_in_root=[MODEL_CREATE_AC])
        tags = {MD5_KEY: self.checksum}

        wi = SSMTWorkItem(item_name=wi_name, command=command, user_files=user_files, tags=tags,
                          related_experiments=[exp_id])

        self.platform.run_items(wi)
        self.wait_till_done(wi)

        if wi.succeeded:
            return wi

    def get_latest_version(self, pkg_name, display_all=False):
        """
        Utility to get the latest version for a given package name
        Args:
            pkg_name: package name given
            display_all: determine if output all package releases
        Returns: the latest version of ven package
        """
        from idmtools_platform_comps.utils.package_version import get_latest_package_version_from_pypi
        from idmtools_platform_comps.utils.package_version import get_latest_package_version_from_artifactory

        latest_version = get_latest_package_version_from_artifactory(pkg_name, display_all)

        if not latest_version:
            latest_version = get_latest_package_version_from_pypi(pkg_name, display_all)

        return latest_version

    def consolidate_requirements(self):
        """
        Combine requiremtns and dynamic requirements (a list):
          - get the latest version of package if version is not provided
          - dynamic requirements will overwrites the requirements file
          
        Returns: the consolidated requirements (as a list)
        """
        import pkg_resources

        req_dict = {}
        comment_list = []
        if self.requirements_path:
            with open(self.requirements_path, 'r') as fd:
                for cnt, line in enumerate(fd):
                    line = line.strip()
                    if line == '':
                        continue

                    if line.startswith('#'):
                        comment_list.append(line)
                        continue

                    req = pkg_resources.Requirement.parse(line)
                    req_dict[req.name] = req.specs

        # pkg_list will overwrite pkg in requirement file
        if self.pkg_list:
            for pkg in self.pkg_list:
                req = pkg_resources.Requirement.parse(pkg)
                req_dict[req.name] = req.specs

        missing_version_dict = {k: v for k, v in req_dict.items() if len(v) == 0 or v[0][1] == ''}
        has_version_dict = {k: v for k, v in req_dict.items() if k not in missing_version_dict}

        update_req_list = []
        for k, v in has_version_dict.items():
            update_req_list.append(f'{k}=={v[0][1]}')

        for k, v in missing_version_dict.items():
            latest = self.get_latest_version(k)
            update_req_list.append(f"{k}=={latest}")

        if self.local_wheels:
            update_req_list.extend([f"Assets/{os.path.basename(whl)}" for whl in self.local_wheels])

        return update_req_list

    def wait_till_done(self, item: IItem, timeout: 'int' = 60 * 60 * 24, refresh_interval: 'int' = 5):
        """
        Wait for the experiment to be done.
        Args:
            refresh_interval: How long to wait between polling.
            timeout: How long to wait before failing.
        """
        import sys
        import time
        from itertools import cycle

        # While they are running, display the status
        animation = cycle(("|", "/", "-", "\\"))

        start_time = time.time()
        while time.time() - start_time < timeout:
            self.platform.refresh_status(item=item)
            sys.stdout.write("\r  {} Waiting {} to finish.".format(next(animation), item.item_type))
            sys.stdout.flush()
            if item.done:
                return item
            time.sleep(refresh_interval)
        raise TimeoutError(f"Timeout of {timeout} seconds exceeded when monitoring item {item.item_type}")
