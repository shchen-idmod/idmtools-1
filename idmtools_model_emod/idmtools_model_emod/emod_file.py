import json
import os
from abc import ABCMeta, abstractmethod
from enum import Enum
from functools import partial
from typing import NoReturn

from idmtools.assets import Asset, AssetCollection, json_handler
from idmtools.utils.filters.asset_filters import file_extension_is


class InputFilesList(AssetCollection, metaclass=ABCMeta):
    def __init__(self, relative_path=None):
        super().__init__()
        self.relative_path = relative_path

    @abstractmethod
    def set_simulation_config(self, simulation):
        pass

    def gather_assets(self):
        assets = [a for a in self.assets if not a.persisted]
        for a in assets:
            a.persisted = True
        return assets


class MigrationTypes(Enum):
    LOCAL = 'Local'
    AIR = 'Air'
    FAMILY = 'Family'
    REGIONAL = 'Regional'
    SEA = 'Sea'


class MigrationFiles(InputFilesList):
    def __init__(self, relative_path=None):
        super().__init__(relative_path)
        self.migration_files = {}

    def add_migration_from_file(self, migration_type: 'MigrationTypes', file_path: 'str'):
        asset = Asset(absolute_path=file_path, relative_path=self.relative_path)
        if asset.extension != "bin":
            raise Exception("Please add the binary (.bin) path for the `add_migration_from_file` function!")
        self.migration_files[migration_type] = asset

    def set_simulation_config(self, simulation):
        # Enable or disable migrations depending on the available files
        for migration_type in MigrationTypes:
            if migration_type in self.migration_files:
                simulation.set_parameter(f"Enable_{migration_type.value}_Migration", 1)
                migration_file = self.migration_files[migration_type]
                simulation.set_parameter(f"{migration_type.value}_Migration_Filename",
                                         os.path.join(migration_file.relative_path, migration_file.filename))
            else:
                simulation.set_parameter(f"Enable_{migration_type.value}_Migration", 0)

    def gather_assets(self):
        for asset in self.migration_files.values():
            self.assets.append(asset)
            self.assets.append(Asset(absolute_path=asset.absolute_path + ".json", relative_path=self.relative_path))

        return super().gather_assets()

    def merge_with(self, mf: 'MigrationFiles', left_precedence: 'bool' = True) -> 'NoReturn':
        if not left_precedence:
            self.migration_files.update(mf.migration_files)
        else:
            for migration_type in set(mf.migration_files.keys()).difference(self.migration_files.keys()):
                self.migration_files[migration_type] = mf.migration_files[migration_type]


class Dlls(InputFilesList):
    def __init__(self):
        super().__init__(relative_path='reporter_plugins')
        self.custom_reports_path = None

    def add_dll(self, dll_path):
        self.add_asset(Asset(absolute_path=dll_path, relative_path=self.relative_path))

    def add_dll_folder(self, dll_folder):
        filter_extensions = partial(file_extension_is, extensions=['dll'])
        self.add_directory(dll_folder, recursive=False, relative_path=self.relative_path, filters=[filter_extensions])

    def set_custom_reports_file(self, custom_reports_path) -> 'NoReturn':
        """
        Add custom reports file.
        Args:
            custom_reports_path: The custom reports file to add(single file).
        """
        self.custom_reports_path = custom_reports_path

    def set_simulation_config(self, simulation):
        if self.custom_reports_path:
            simulation.set_parameter("Custom_Reports_Filename", os.path.basename(self.custom_reports_path))
            simulation.assets.add_asset(Asset(absolute_path=self.custom_reports_path))


class DemographicsFiles(InputFilesList):
    def set_simulation_config(self, simulation):
        simulation.config["Demographics_Filenames"] = [os.path.join(df.relative_path, df.filename) for df in
                                                       self.assets]

    def add_demographics_from_file(self, absolute_path, filename: 'str' = None):
        filename = filename or os.path.basename(absolute_path)
        with open(absolute_path, 'r') as fp:
            asset = Asset(filename=filename, content=json.load(fp), relative_path=self.relative_path,
                          absolute_path=absolute_path, handler=json_handler)

        if asset in self.assets:
            raise Exception("Duplicated demographics file")

        self.assets.append(asset)

    def add_demographics_from_dict(self, content, filename):
        asset = Asset(filename=filename, content=content, relative_path=self.relative_path, handler=json_handler)
        if asset in self.assets:
            raise Exception("Duplicated demographics file")

        self.assets.append(asset)
