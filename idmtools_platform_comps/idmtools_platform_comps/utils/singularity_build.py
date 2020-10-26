import hashlib
import io
import json
import os
from dataclasses import dataclass, field, InitVar
from typing import List, Dict, NoReturn, Union
from urllib.parse import urlparse
from uuid import UUID

from COMPS.Data import QueryCriteria

from idmtools.assets import AssetCollection
from idmtools.assets.file_list import FileList
from idmtools.core import EntityStatus
from idmtools.entities.relation_type import RelationType
from idmtools.utils.hashing import calculate_md5_stream
from idmtools_platform_comps.ssmt_work_items.comps_workitems import InputDataWorkItem
from idmtools_platform_comps.utils.package_version import get_docker_manifest, get_digest_from_docker_hub

SB_BASE_WORKER_PATH = os.path.join(os.path.dirname(__file__), 'base_singularity_work_order.json')


@dataclass(repr=False)
class SingularityBuildWorkItem(InputDataWorkItem):
    #: Path to definition file
    definition_file: str = field(default=None)
    #: Image Url
    image_url: InitVar[str] = None
    #: Destination image name
    image_name: str = field(default=None)
    #: Name of the workitem
    name: str = field(default=None)
    #: Tages to add to container asset collection
    image_tags: Dict[str, str] = field(default_factory=dict)
    #: Allows you to set a different library. (The default library is “https://library.sylabs.io”). See https://sylabs.io/guides/3.5/user-guide/cli/singularity_build.html
    library: str = field(default=None)
    #: only run specific section(s) of definition file (setup, post, files, environment, test, labels, none) (default [all])
    section: List[str] = field(default_factory=lambda: ['all'])
    #: build using user namespace to fake root user (requires a privileged installation)
    fix_permissions: bool = field(default=False)
    # AssetCollection created by build
    asset_collection: AssetCollection = field(default=None)
    #: Additional Mounts
    additional_mounts: List[str] = field(default_factory=list)
    #: Environment vars for remote build
    environment_variables: Dict[str, str] = field(default_factory=dict)
    #: Force build
    force: bool = field(default=False)
    #: Don't include default tags
    disable_default_tags: bool = field(default=None)

    #: loaded if url is docker://. Used to determine if we need to re-run a build
    __docker_digest: Dict[str, str] = field(default=None)
    __docker_tag: str = field(default=None)

    def __post_init__(self, item_name: str, asset_collection_id: UUID, asset_files: FileList, user_files: FileList, image_url: str):
        if self.name is None:
            self.name = "Singularity build"
        self.work_item_type = 'ImageBuilderWorker'
        super().__post_init__(item_name, asset_collection_id, asset_files, user_files)

        self.image_url = image_url if isinstance(image_url, str) else None

    def get_container_info(self) -> Dict[str, str]:
        pass

    @property
    def image_url(self):
        return self._image_url

    @image_url.setter
    def image_url(self, value: str):
        url_info = urlparse(value)
        if url_info.scheme == "docker":
            if "packages.idmod.org" in value:
                full_manifest, self.__docker_tag = get_docker_manifest(url_info.path)
                self.__docker_digest = full_manifest['config']['digest']
            else:
                self.__docker_tag = url_info.netloc + ":latest" if ":" not in value else url_info.netloc
                image, tag = url_info.netloc.split(":")
                self.__docker_digest = get_digest_from_docker_hub(image, tag)
            if self.fix_permissions:
                self.__docker_digest += "--fix-perms"
            if self.name is None:
                self.name = f"Load Singularity image from Docker {self.__docker_tag}"
        # TODO how to do this for shub
        self._image_url = value

    def context_checksum(self) -> str:
        file_hash = hashlib.sha256()

        for asset in sorted(self.assets + self.transient_assets, key=lambda a: a.short_remote_path()):
            if asset.absolute_path:
                with open(asset.absolute_path, mode='rb') as ain:
                    calculate_md5_stream(ain, file_hash=file_hash)
            else:
                item = io.BytesIO()
                item.write(asset.bytes)
                item.seek(0)
                calculate_md5_stream(item, file_hash=file_hash)

        if len(self.environment_variables):
            contents = json.dumps(self.environment_variables, sort_keys=True)
            item = io.BytesIO()
            item.write(contents.encode('utf-8'))
            item.seek(0)
            calculate_md5_stream(item, file_hash=file_hash)
        if self.definition_file and os.path.exists(self.definition_file):
            with open(self.definition_file, mode='rb') as ain:
                calculate_md5_stream(ain, file_hash=file_hash)
        return file_hash.hexdigest()

    @staticmethod
    def find_existing_container(sbi: 'SingularityBuildWorkItem'):
        if sbi.__docker_digest:
            ac = sbi.platform._assets.get(None, query_criteria=QueryCriteria().where_tag(['type=singularity', f'docker_digest={sbi.__docker_digest}']))
            return ac if ac else None
        return None

    def __add_tags(self):
        self.image_tags['type'] = 'singularity'
        if not self.disable_default_tags:
            if self.__docker_digest and isinstance(self.__docker_digest, str):
                self.image_tags['docker_digest'] = self.__docker_digest
                self.image_tags['docker_from'] = self.__docker_tag
                if self.image_name is None:
                    self.image_name = self.__docker_tag.strip(" /").replace(":", "_").replace("/", "_") + ".sif"
            elif self.definition_file:
                self.image_tags['build_context'] = self.context_checksum()

            if self.image_url:
                self.image_tags['image_url'] = self.image_url

    def _prep_workorder_before_create(self):
        """
        """
        self.__add_tags()
        self.load_work_order(SB_BASE_WORKER_PATH)
        if self.definition_file:
            self.work_order['Build']['Input'] = os.path.basename(self.definition_file)
        else:
            self.work_order['Build']['Input'] = self.image_url
        if len(self.environment_variables):
            self.work_order['Build']['StaticEnvironment'] = self.environment_variables
        if len(self.additional_mounts):
            self.work_order['Build']['AdditionalMounts'] = self.additional_mounts
        self.work_order['Build']['Output'] = self.image_name if self.image_name else "image.sif"
        self.work_order['Build']['Tags'] = self.image_tags
        self.work_order['Build']['Flags'] = dict()
        if self.fix_permissions:
            self.work_order['Build']['Flags']['Switches'] = ["--fix-perms"]
        if self.library:
            self.work_order['Build']['Flags']['--library'] = self.library
        if self.section:
            self.work_order['Build']['Flags']['--section'] = self.section
        return self.work_order

    def pre_creation(self, platform: 'IPlatform') -> None:
        super(SingularityBuildWorkItem, self).pre_creation(platform)
        self._prep_workorder_before_create()

    def __fetch_finished_asset_collection(self, platform: 'IPlatform') -> Union[AssetCollection, None]:
        comps_workitem = self.get_platform_object(force=True)
        acs = comps_workitem.get_related_asset_collections(RelationType.Created)
        if acs:
            self.asset_collection = AssetCollection.from_id(acs[0].id, platform=platform if platform else self.platform)
            return self.asset_collection
        return None

    def run(self, wait_until_done: bool = False, platform: 'IPlatform' = None, wait_on_done_progress: bool = True, wait_on_done: bool = True, **run_opts) -> NoReturn:
        """

        Args:
            wait_until_done:
            platform:
            wait_on_done_progress:
            wait_on_done:
            **run_opts:

        Returns:

        """
        p = super()._check_for_platform_from_context(platform)
        opts = dict(wait_on_done_progress=wait_on_done_progress, wait_until_done=wait_until_done, wait_on_done=wait_on_done, platform=p)
        self.platform = p
        ac = self.find_existing_container(self)
        if ac is None:
            super().run(**opts)
        else:
            self.asset_collection = ac

    def wait(self, wait_on_done_progress: bool = True, timeout: int = None, refresh_interval=None, platform: 'IPlatform' = None) -> Union[AssetCollection, None]:
        """
        Waits on Singularity Build Workitem to finish and fetches the resulting asset collection

        Args:
            wait_on_done_progress: When set to true, a progress bar will be shown from the item
            timeout: Timeout for waiting on item. If none, wait will be forever
            refresh_interval: How often to refresh progress
            platform: Platform

        Returns:
            AssetCollection created if item succeeds
        """
        # wait on related items before we wait on our item
        p = super()._check_for_platform_from_context(platform)
        opts = dict(wait_on_done_progress=wait_on_done_progress, timeout=timeout, refresh_interval=refresh_interval, platform=p)

        super().wait(**opts)
        if self.status == EntityStatus.SUCCEEDED:
            return self.__fetch_finished_asset_collection(p)
