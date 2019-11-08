import copy
import os
import typing
from dataclasses import dataclass, field

from idmtools.entities import IExperiment, CommandLine
from idmtools_model_emod.emod_file import DemographicsFiles
from idmtools_model_emod.emod_simulation import EMODSimulation

if typing.TYPE_CHECKING:
    from idmtools_model_emod.defaults import iemod_default


@dataclass(repr=False)
class EMODExperiment(IExperiment):
    eradication_path: str = field(default=None, compare=False, metadata={"md": True})
    legacy_exe: 'bool' = field(default=False, metadata={"md": True})
    demographics: 'DemographicsFiles' = field(default_factory=lambda: DemographicsFiles('demographics'))

    def __post_init__(self, simulation_type):
        super().__post_init__(simulation_type=EMODSimulation)
        if self.eradication_path is not None:
            self.eradication_path = os.path.abspath(self.eradication_path)

    @classmethod
    def from_default(cls, name, default: 'iemod_default', eradication_path=None):
        exp = cls(name=name, eradication_path=eradication_path)

        # Set the base simulation
        default.process_simulation(exp.base_simulation)

        # Add the demographics
        for filename, content in default.demographics().items():
            exp.demographics.add_demographics_from_dict(content=content, filename=filename)

        return exp

    @classmethod
    def from_files(cls, name, eradication_path=None, config_path=None, campaign_path=None, demographics_paths=None):
        """
        Load custom |EMOD_s| files when creating :class:`EMODExperiment`.

        Args:
            name: The experiment name.
            eradication_path: The eradication.exe path.
            config_path: The custom configuration file.
            campaign_path: The custom campaign file.
            demographics_paths: The custom demographics files (single file or a list).

        Returns: An initialized experiment
        """
        # Create the experiment
        exp = cls(name=name, eradication_path=eradication_path)

        # Load the files
        exp.base_simulation.load_files(config_path=config_path, campaign_path=campaign_path)

        if demographics_paths:
            for demog_path in [demographics_paths] if isinstance(demographics_paths, str) else demographics_paths:
                exp.demographics.add_demographics_from_file(demog_path)

        return exp

    def gather_assets(self) -> None:
        from idmtools.assets import Asset

        # Add Eradication.exe to assets
        self.assets.add_asset(Asset(absolute_path=self.eradication_path), fail_on_duplicate=False)

        # Add demographics to assets
        self.assets.extend(self.demographics.gather_assets())

    def pre_creation(self):
        super().pre_creation()

        # Create the command line according to the location of the model
        model_executable = os.path.basename(self.eradication_path)

        # Input path is different for legacy exes
        input_path = "./Assets\;." if not self.legacy_exe else "./Assets"

        # We have everything we need for the command, create the object
        self.command = CommandLine(f"Assets/{model_executable}", "--config config.json", f"--input-path {input_path}",
                                   f"--dll-path ./Assets")

    def add_dll_files(self, dll_files_path):
        reporter_path = "reporter_plugins"
        if os.path.isfile(dll_files_path):
            from functools import partial
            from idmtools.utils.filters.asset_filters import file_name_is

            dll_files_dirname = os.path.dirname(dll_files_path)
            dll_files_basename = os.path.basename(dll_files_path)
            filter_name = partial(file_name_is, filenames=[dll_files_basename])
            self.assets.add_directory(assets_directory=dll_files_dirname, filters=[filter_name],
                                      relative_path=reporter_path)
        elif os.path.isdir(dll_files_path):
            dir_list = next(os.walk(dll_files_path))[1]
            if reporter_path in dir_list:
                self.assets.add_directory(assets_directory=os.path.join(dll_files_path, reporter_path),
                                          relative_path=reporter_path)
            else:
                self.assets.add_directory(assets_directory=dll_files_path, relative_path=reporter_path)
        else:
            raise FileNotFoundError(f"No such file or directory: {dll_files_path}")

    def simulation(self):
        simulation = super().simulation()
        # Copy the experiment demographics and set them as persisted to prevent change
        # TODO: change persisted to the frozen mechanism when done
        demog_copy = copy.deepcopy(self.demographics)
        demog_copy.set_all_persisted()
        # Add them to the simulation
        simulation.demographics.extend(demog_copy)
        return simulation
