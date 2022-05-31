"""
Here we implement the JSON Metadata operations.

Copyright 2021, Bill & Melinda Gates Foundation. All rights reserved.
"""
import json
from pathlib import Path
from typing import Dict, List, Type, Union
from dataclasses import dataclass, field
from idmtools.core.interfaces.ientity import IEntity
from idmtools.core import ItemType
from idmtools.core.interfaces import imetadata_operations
from idmtools.entities import Suite
from idmtools.entities.experiment import Experiment
from idmtools.entities.simulation import Simulation
from idmtools.utils.json import IDMJSONEncoder


@dataclass
class JSONMetadataOperations(imetadata_operations.IMetadataOperations):
    platform: 'platform'  # noqa: F821
    platform_type: Type = field(default=None)
    metadata_filename: str = field(default='metadata.json')

    @staticmethod
    def _read_from_file(filepath: Union[Path, str]) -> Dict:
        """
        Utility: read metadata from a file.
        Args:
            filepath: metadata file path
        Returns:
            JSON
        """
        filepath = Path(filepath)
        with filepath.open(mode='r') as f:
            metadata = json.load(f)
        return metadata

    @staticmethod
    def _write_to_file(filepath: Union[Path, str], data: Dict) -> None:
        """
        Utility: save metadata to a file.
        Args:
            filepath: metadata file path
            data: metadata as dictionary
        Returns:
            None
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with filepath.open(mode='w') as f:
            json.dump(data, f, cls=IDMJSONEncoder)

    def get_metadata_filepath(self, item: IEntity) -> Path:
        """
        Retrieve item's metadata file path.
        Args:
            item: idmtools entity (Suite, Experiment and Simulation, etc.)
        Returns:
            item's metadata file path
        """
        if not isinstance(item, (Suite, Experiment, Simulation)):
            raise RuntimeError(f"get_metadata_filepath method supports Suite/Experiment/Simulation only.")
        item_dir = self.platform._op_client.get_directory(item)
        filepath = Path(item_dir, self.metadata_filename)
        return filepath

    def get(self, item: Union[Suite, Experiment, Simulation]) -> Dict:
        """
        Obtain item's metadata.
        Args:
            item: idmtools entity (Suite, Experiment and Simulation, etc.)
        Returns:
             key/value dict of metadata from the given item
        """
        if not isinstance(item, (Suite, Experiment, Simulation)):
            raise RuntimeError(f"Get method supports Suite/Experiment/Simulation only.")
        meta = json.loads(json.dumps(item.to_dict(), cls=IDMJSONEncoder))
        return meta

    def dump(self, item: Union[Suite, Experiment, Simulation]) -> None:
        """
        Save item's metadata to a file.
        Args:
            item: idmtools entity (Suite, Experiment and Simulation, etc.)
        Returns:
            None
        """
        if not isinstance(item, (Suite, Experiment, Simulation)):
            raise RuntimeError(f"Dump method supports Suite/Experiment/Simulation only.")
        dest = self.get_metadata_filepath(item)
        meta = self.get(item)
        self._write_to_file(dest, meta)

    def load(self, item: Union[Suite, Experiment, Simulation]) -> Dict:
        """
        Obtain item's metadata file.
        Args:
            item: idmtools entity (Suite, Experiment and Simulation, etc.)
        Returns:
             key/value dict of metadata from the given item
        """
        if not isinstance(item, (Suite, Experiment, Simulation)):
            raise RuntimeError(f"Load method supports Suite/Experiment/Simulation only.")
        meta_file = self.get_metadata_filepath(item)
        meta = self._read_from_file(meta_file)
        return meta

    def load_from_file(self, metadata_filepath: Union[Path, str]) -> Dict:
        """
        Obtain the metadata for the given filepath.
        Args:
            metadata_filepath: str
        Returns:
             key/value dict of metadata from the given filepath
        """
        if not (Path(metadata_filepath).exists()):
            raise RuntimeError(f"File not found: '{metadata_filepath}'.")
        meta = self._read_from_file(metadata_filepath)
        return meta

    def update(self, item: Union[Suite, Experiment, Simulation], metadata: Dict = {}, override=True) -> None:
        """
        Update or replace item's metadata file.
        Args:
            item: idmtools entity (Suite, Experiment and Simulation, etc.)
            metadata: dict to be updated
            override: True/False
        Returns:
             None
        """
        if not isinstance(item, (Suite, Experiment, Simulation)):
            raise RuntimeError(f"Set method supports Suite/Experiment/Simulation only.")
        meta = metadata
        if not override:
            meta = self.load(item)
            meta.update(metadata)
        meta_file = self.get_metadata_filepath(item)
        self._write_to_file(meta_file, meta)

    def clear(self, item: IEntity) -> None:
        """
        Clear the item's metadata file.
        Args:
            item: clear the item's metadata file
        Returns:
            None
        """
        if not isinstance(item, (Suite, Experiment, Simulation)):
            raise RuntimeError(f"Clear method supports Suite/Experiment/Simulation only.")
        self.update(item=item, metadata={}, override=True)

    def get_children(self, item: IEntity) -> List[Dict]:
        """
        Fetch item's children.
        Args:
            item: idmtools entity (Suite, Experiment)
        Returns:
            Lis of metadata
        """
        if not isinstance(item, (Suite, Experiment)):
            raise RuntimeError(f"Get children method supports Suite and Experiment only.")
        item_list = []
        item_dir = self.platform._op_client.get_directory(item)
        pattern = f'*/{self.metadata_filename}'
        for meta_file in item_dir.glob(pattern=pattern):
            meta = self.load_from_file(meta_file)
            item_list.append(meta)
        return item_list

    def get_all(self, item_type: ItemType) -> List[Dict]:
        """
        Obtain all the metadata for a given item type.
        Args:
            item_type: the type of metadata to search for matches (simulation, experiment, suite, etc)
        Returns:
            list of metadata with given item type
        """
        if item_type is ItemType.SIMULATION:
            pattern = f"*/*/*/{self.metadata_filename}"
        elif item_type is ItemType.EXPERIMENT:
            pattern = f"*/*/{self.metadata_filename}"
        elif item_type is ItemType.SUITE:
            pattern = f"*/{self.metadata_filename}"
        else:
            raise RuntimeError(f"Unknown item type: {item_type}")
        item_list = []
        root = Path(self.platform.job_directory)
        for meta_file in root.glob(pattern=pattern):
            meta = self.load_from_file(meta_file)
            item_list.append(meta)
        return item_list

    @staticmethod
    def _match_filter(item: Dict, metadata: Dict):
        """
        Utility: verify if item match metadata.
        Args:
            item: dict represents metadata of Suite/Experiment/Simulation
            metadata: dict as a filter
        Returns:
            list of Dict items
        """
        is_match = all([k in item and item[k] == v for k, v in metadata.items()])
        return is_match

    def filter(self, item_type: ItemType, property_filter: Dict = None, tag_filter: Dict = None,
               items: List = None) -> List[Dict]:
        """
        Obtain all items that match the given properties key/value pairs passed.
        The two filters are applied on item with 'AND' logical checking.
        Args:
            item_type: the type of items to search for matches (simulation, experiment, suite, etc)
            property_filter: a dict of metadata key/value pairs for exact match searching
            tag_filter: a dict of metadata key/value pairs for exact match searching
            items: list
        Returns:
            a list of metadata matching the properties ke/value with given item type
        """
        if items is None:
            items = self.get_all(item_type)
        item_list = []
        for item in items:
            is_match = True
            if property_filter:
                is_match = self._match_filter(item, property_filter)
            if tag_filter:
                is_match = is_match and self._match_filter(item['tags'], tag_filter)
            if is_match:
                item_list.append(item)
        return item_list
