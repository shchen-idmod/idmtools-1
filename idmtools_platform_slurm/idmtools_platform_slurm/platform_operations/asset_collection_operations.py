"""
Here we implement the SlurmPlatform asset collection operations.

Copyright 2021, Bill & Melinda Gates Foundation. All rights reserved.
"""
import shutil
from uuid import UUID
from pathlib import Path
from dataclasses import field, dataclass
from logging import getLogger
from typing import Type, List, Dict, Union, Optional
from idmtools.assets import AssetCollection, Asset
from idmtools.entities.experiment import Experiment
from idmtools.entities.simulation import Simulation
from idmtools.entities.iplatform_ops.iplatform_asset_collection_operations import IPlatformAssetCollectionOperations

logger = getLogger(__name__)
user_logger = getLogger("user")

EXCLUDE_FILES = ['_run.sh', 'metadata.json', 'stdout.txt', 'stderr.txt', 'status.txt']


@dataclass
class SlurmPlatformAssetCollectionOperations(IPlatformAssetCollectionOperations):
    """
    Provides AssetCollection Operations to SlurmPlatform.
    """
    platform: 'SlurmPlatform'  # noqa F821
    platform_type: Type = field(default=None)

    def get(self, asset_collection_id: Optional[UUID], **kwargs) -> AssetCollection:
        """
        Get an asset collection by id.
        Args:
            asset_collection_id: id of asset collection
            kwargs: keyword arguments used to expand functionality.
        Returns:
            AssetCollection
        """
        raise NotImplementedError("Get asset collection is not supported on SlurmPlatform.")

    def platform_create(self, asset_collection: AssetCollection, **kwargs) -> AssetCollection:
        """
        Create AssetCollection.
        Args:
            asset_collection: AssetCollection to create
            kwargs: keyword arguments used to expand functionality.
        Returns:
            AssetCollection
        """
        raise NotImplementedError("platform_create is not supported on SlurmPlatform.")

    def link_common_assets(self, simulation: Simulation, common_asset_dir: Union[Path, str] = None) -> None:
        """
        Link directory/files.
        Args:
            simulation: Simulation
            common_asset_dir: the common asset folder path
        Returns:
            None
        """
        if common_asset_dir is None:
            common_asset_dir = Path(self.platform._op_client.get_directory(simulation.parent), 'Assets')
        link_dir = Path(self.platform._op_client.get_directory(simulation), 'Assets')
        self.platform._op_client.link_dir(common_asset_dir, link_dir)

    def get_assets(self, item: Union[Experiment, Simulation], files: List[str], **kwargs) -> Dict[str, bytearray]:
        """
        Get assets for simulation.
        Args:
            item: Experiment/Simulation
            files: files to be retrieved
            kwargs: keyword arguments used to expand functionality.
        Returns:
            Dict[str, bytearray]
        """
        ret = dict()
        if isinstance(item, Simulation):
            sim_dir = self.platform._op_client.get_directory(item)
            for file in files:
                asset_file = Path(sim_dir, file)
                if asset_file.exists():
                    asset = Asset(absolute_path=asset_file.absolute())
                    ret[file] = bytearray(asset.bytes)
                else:
                    raise RuntimeError(f"Couldn't find asset for path '{file}'.")
        elif isinstance(item, Experiment):
            for sim in item.simulations:
                ret[sim.id] = self.get_assets(sim, files, **kwargs)
        else:
            raise NotImplementedError(f"get_assets() for items of type {type(item)} is not supported on SlurmPlatform.")

        return ret

    def list_assets(self, item: Union[Experiment, Simulation], exclude: List[str] = None, **kwargs) -> List[Asset]:
        """
        List assets for Experiment/Simulation.
        Args:
            item: Experiment/Simulation
            exclude: list of file path
            kwargs: keyword arguments used to expand functionality.
        Returns:
            list of Asset
        """
        exclude = exclude if exclude is not None else EXCLUDE_FILES
        assets = []
        if isinstance(item, Experiment):
            assets_dir = Path(self.platform._op_client.get_directory(item), 'Assets')
        elif isinstance(item, Simulation):
            assets_dir = self.platform._op_client.get_directory(item)
        else:
            raise NotImplementedError("List assets for this item is not supported on SlurmPlatform.")

        for asset_file in assets_dir.iterdir():
            if asset_file.is_file() and asset_file.name not in exclude:
                asset = Asset(absolute_path=asset_file.absolute())
                assets.append(asset)
        return assets

    def copy_asset(self, src: Union[Asset, Path, str], dest: Union[Path, str]) -> None:
        """
        Copy asset/file to destination.
        Args:
            src: the file content
            dest: the file path
        Returns:
            None
        """
        if isinstance(src, Asset):
            if src.absolute_path:
                shutil.copy(src.absolute_path, dest)
            elif src.content:
                dest_filepath = Path(dest, src.filename)
                dest_filepath.write_bytes(src.bytes)
        else:
            shutil.copy(src, dest)

    def dump_assets(self, item: Union[Experiment, Simulation], **kwargs) -> None:
        """
        Dump item's assets.
        Args:
            item: Experiment/Simulation
            kwargs: keyword arguments used to expand functionality.
        Returns:
            None
        """
        if isinstance(item, Experiment):
            exp_asset_dir = Path(self.platform._op_client.get_directory(item), 'Assets')
            self.platform._op_client.mk_directory(dest=exp_asset_dir)
            for asset in item.assets:
                self.platform._op_client.mk_directory(dest=exp_asset_dir.joinpath(asset.relative_path))
                self.copy_asset(asset, exp_asset_dir.joinpath(asset.relative_path))

                # Make Eradication executable
                if asset.filename.lower() == 'eradication':
                    self.platform._op_client.update_script_mode(asset.absolute_path)

        elif isinstance(item, Simulation):
            exp_dir = self.platform._op_client.get_directory(item.parent)
            for asset in item.assets:
                sim_dir = Path(exp_dir, item.id)
                self.copy_asset(asset, sim_dir)
        else:
            raise NotImplementedError(f"dump_assets() for item of type {type(item)} is not supported on SlurmPlatform.")
