"""
This is SlurmPlatform operations utils.

Copyright 2021, Bill & Melinda Gates Foundation. All rights reserved.
"""
import os
import copy
import json
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple, Union, TYPE_CHECKING
from dataclasses import dataclass, field
from idmtools.entities.experiment import Experiment
from idmtools.entities.simulation import Simulation
from idmtools_platform_slurm.slurm_operations.slurm_constants import SLURM_MAPS
from idmtools.core import ItemType
from logging import getLogger

if TYPE_CHECKING:  # pragma: no cover
    from idmtools.entities.iplatform import IPlatform

logger = getLogger(__name__)


def check_slurm_job(platform: 'IPlatform', scope: Tuple[str, ItemType] = None, status_filter: List = None,
                    job_ids: Union[str, List[str]] = None, display_count: int = 20, verbose: bool = True,
                    root: str = 'sim', display: bool = True):
    sv = status_viewer(scope=scope)
    sv.output_status(platform, status_filter=status_filter, job_ids=job_ids, display_count=display_count,
                     verbose=verbose, root=root, display=display)


@dataclass(repr=False)
class status_viewer:
    """
    A class to wrap the functions involved in retrieve simulations status.
    """
    scope: Tuple[str, ItemType] = field(default=None)

    _exp: Experiment = field(default=None, init=False, compare=False)
    _sim: Simulation = field(default=None, init=False, compare=False)
    _summary: Dict = field(default_factory=dict, init=False, compare=False)

    _job_dict: Dict = field(default_factory=dict, init=False, compare=False)
    _job_list: List = field(default_factory=list, init=False, compare=False)
    _sim_no_status: List = field(default_factory=list, init=False, compare=False)

    _simulations: List = field(default_factory=list, init=False, compare=False)
    _status_list: Dict = field(default_factory=list, init=False, compare=False)
    _simulation_count: int = field(default=None, init=False, compare=False)

    def build_summary(self, job_id, suite_id, experiment_id, job_directory):
        return dict(job_id=job_id, suite=suite_id, experiment=experiment_id, job_directory=job_directory)

    def initialize(self, platform: 'IPlatform') -> Dict:
        """
        Build simulations status dictionary.
        Args:
            platform: idmtools Platform
        Returns:
            None
        """
        if self.scope is not None:
            item = platform.get_item(self.scope[0], self.scope[1])
            if self.scope[1] == ItemType.SUITE:
                self._exp = item.experiments[0]  # only consider the first experiment
            elif self.scope[1] == ItemType.EXPERIMENT:
                self._exp = item
            elif self.scope[1] == ItemType.SIMULATION:
                self._sim = item
                self._exp = item.parent
            else:
                raise RuntimeError('Only support Suite/Experiment/Simulation.')
        else:
            # take the last suite as the search scope
            try:
                last_suite_dir = max(Path(platform.job_directory).glob('*/'), key=os.path.getmtime)
            except:
                raise FileNotFoundError("Could not find the last Suite!")

            batch_dir = max(Path(last_suite_dir).glob('*/sbatch.sh'), key=os.path.getmtime)
            exp_dir = Path(batch_dir).parent
            exp_id = exp_dir.name
            self._exp = platform.get_item(exp_id, ItemType.EXPERIMENT)

            print('------------------------------')
            print('last_suite_dir: ', last_suite_dir)
            print('last_experiment_dir: ', exp_id)
            print('------------------------------')

        job_id_path = platform.get_directory(self._exp).joinpath('job_id.txt')
        job_id = open(job_id_path).read().strip()
        self._summary = dict(job_id=job_id, suite=self._exp.parent.id, experiment=self._exp.id,
                             job_directory=platform.job_directory)

        if self._sim:
            self._simulations = [self._sim]
            self._simulation_count = len(self._sim.parent.simulations)
        elif self._exp:
            self._simulations = self._exp.simulations
            self._simulation_count = len(self._simulations)

    def apply_filters(self, platform: 'IPlatform', status_filter: List = None, job_ids: Union[str, List[str]] = None,
                      verbose: bool = True, root: str = 'sim'):
        """
        Filter results.
        Args:
            platform: idmtools Platform
            status_filter: tuple with target status
            job_ids: slurm job ids
            verbose: True/False to include simulation directory
            root: dictionary root key: 'sim' or 'job'
        Returns:
            None
        """

        if status_filter is None:
            status_filter = ['0', '-1', '100']

        self._job_dict = {}
        self._job_list = []
        self._status_list = []

        for sim in self._simulations:
            sim_dir = platform.get_directory(sim)
            job_status_path = sim_dir.joinpath("job_status.txt")
            if job_status_path.exists():
                job_id_path = sim_dir.joinpath('job_id.txt')
                if job_id_path.exists():
                    job_id = open(job_id_path).read().strip()
                else:
                    job_id = None

                status = open(job_status_path).read().strip()
                if status not in status_filter:
                    continue

                if job_ids is not None and job_id not in job_ids:
                    continue

                self._status_list.append(status)
                if root == 'job':
                    # job_id as root
                    d = dict(sim=sim.id, status=status)
                    if verbose:
                        d["WorkDir"] = str(platform.get_directory(sim))
                    self._job_dict[job_id] = d
                    self._job_list.append(job_id)
                elif root == 'sim':
                    # sim_id as root
                    d = dict(job_id=job_id, status=status)
                    if verbose:
                        d["WorkDir"] = str(platform.get_directory(sim))
                    self._job_dict[sim.id] = d
                    self._job_list.append(sim.id)
            else:
                self._sim_no_status.append(sim.id)

    @staticmethod
    def output_definition() -> None:
        """
        Output the status definitions.
        """
        slurm_map = copy.deepcopy(SLURM_MAPS)
        slurm_map.pop('None', None)
        print('------------------------------')
        print("STATUS DEFINITION")
        print("0: ".ljust(20), slurm_map['0'].name)
        print("-1: ".ljust(20), slurm_map['-1'].name)
        print("100: ".ljust(20), slurm_map['100'].name)
        print('------------------------------')

    def output_summary(self) -> None:
        """
        Output job/experiment id/dir.
        Returns:
            None
        """
        if self._summary:
            print("job_id: ".ljust(20), self._summary["job_id"])
            print("suite: ".ljust(20), self._summary["suite"])
            print("experiment: ".ljust(20), self._summary["experiment"])
            print("job_directory: ".ljust(20), self._summary["job_directory"])

    def output_status(self, platform: 'IPlatform', status_filter: List = None, job_ids: Union[str, List[str]] = None,
                      verbose: bool = True, root: str = 'job', display: bool = True, display_count: int = 20) -> None:
        """
        Output simulations status with possible override parameters.

        Args:
            platform: idmtools Platform
            status_filter: tuple with target status
            job_ids: slurm job ids
            verbose: True/False to include simulation directory
            root: dictionary root key: 'sim' or 'job'
            display: True/False to print the searched results
            display_count: how many to print
        Returns:
            None
        """
        self.initialize(platform)
        self.apply_filters(platform, status_filter, job_ids, verbose, root)
        self.output_summary()

        if display:
            if display_count is None or len(self._job_dict) <= display_count:
                show_job_dict = self._job_dict
            else:
                show_job_list = self._job_list[0: display_count]
                show_job_dict = {id: job for id, job in self._job_dict.items() if id in show_job_list}

            print(json.dumps(show_job_dict, indent=3))
        self.output_definition()

        _simulation_count = len(self._simulations)
        if display and len(self._job_dict) > display_count:
            print(f"ONLY DISPLAY {display_count} ITEMS")
        print("status_filter: ".ljust(20), status_filter)
        print("verbose: ".ljust(20), verbose)
        print("display: ".ljust(20), display)
        print("Simulation Count: ".ljust(20), _simulation_count)
        print("Match Count: ".ljust(20), len(self._job_dict), f' ({dict(Counter(self._status_list))})')
        print("Not Match Count: ".ljust(20), _simulation_count - len(self._job_dict))
        print("No Status Count: ".ljust(20), len(self._sim_no_status))

        if self._sim:
            print('\nSimulation Status: ', self._sim.status.name)
        elif self._exp:
            print('\nExperiment Status: ', self._exp.status.name)


# def check_slurm_job(platform, scope: Tuple[str, ItemType] = None, status_filter: List = None,
#                     job_ids: Union[str, List[str]] = None, display_count: int = 20, verbose: bool = True,
#                     root: str = 'job', display: bool = True):
#     sv = status_viewer(scope=scope, status_filter=status_filter, job_ids=job_ids, display_count=display_count, verbose=verbose, root=root, display=display)
#     sv.output_status(platform)

if __name__ == "__main__":
    from idmtools.core.platform_factory import Platform

    # platform = Platform('SLURM_LOCAL', job_directory=r'C:\Projects\idmtools\examples\python_model\DEST1')
    platform = Platform('SLURM_LOCAL', job_directory=r'C:\Projects\idmtools_zhaowei\examples\python_model\DEST1')
    # platform = Platform('SLURM_LOCAL', job_directory='/home/schen/example_mmq')
    # platform = Platform('SLURM_LOCAL', job_directory='/home/zdf1921/JOB_TEST')

    # # Case: check the latest
    # sv = status_viewer()
    #
    # sv = status_viewer(status_filter=['0', '-1'])
    #
    # sv = status_viewer(display_count=10)
    #
    # sv = status_viewer(root='sim')
    #
    # # Case: given Suite
    # sv = status_viewer(status_filter=['100', '0'], scope=("821553b4-640b-40ee-80f5-fd20af5f0d7d", ItemType.SUITE), display_count=10)
    #
    # # Case: given job_id, Experiment (job_id has higher place)
    # sv = status_viewer(status_filter=['100', '0'], job_ids=['74892_1', '74892_2'], scope=("d9cda43b-7b6e-4d2f-a302-fde0e38bb840", ItemType.EXPERIMENT), display_count=10)
    #
    # # Case: given Experiment
    # sv = status_viewer(status_filter=['100', '0'], scope=("d9cda43b-7b6e-4d2f-a302-fde0e38bb840", ItemType.EXPERIMENT), display_count=10)

    # # Case: given Simulation
    # sv = status_viewer(status_filter=['100', '0'], scope=("844062d0-224b-4d55-a043-fc4b00f13d0b", ItemType.SIMULATION), display_count=10)
    #
    # # Case: give job_id no scope (find from the latest)
    # sv = status_viewer(job_ids=['74892_1', '74892_2'], display_count=10, root='sim')  # default: root='job'
    #
    # # Case: give job_id with scope
    # sv = status_viewer(job_ids=['74892_1', '74892_2'], scope=("844062d0-224b-4d55-a043-fc4b00f13d0b", ItemType.SIMULATION), display_count=10, verbose=False)

    # sv = status_viewer()
    # sv.output_status(platform)
    # sv.output_status(platform, root='job')
    # sv.output_status(platform, display_count=1)
    # sv.output_status(platform, root='job', display_count=1)

    check_slurm_job(platform)
    # check_slurm_job(platform, job_ids=['74892_1', '74892_2'], display_count=10, root='sim')
    # check_slurm_job(platform, job_ids=['74892_1', '74892_2'], display_count=10, root='job')
    # check_slurm_job(platform, job_ids=['74892_100', '74892_200'], display_count=10, root='sim')  # latest experiment
    # check_slurm_job(platform, scope=("d9cda43b-7b6e-4d2f-a302-fde0e38bb840", ItemType.EXPERIMENT))
