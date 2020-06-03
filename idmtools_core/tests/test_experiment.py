import itertools
import unittest

from idmtools.builders import SimulationBuilder
from idmtools.core.enums import EntityStatus
from idmtools.entities.experiment import Experiment
from idmtools.entities.templated_simulation import TemplatedSimulations
from idmtools_models.python.json_python_task import JSONConfiguredPythonTask
from idmtools_test.utils.test_task import TestTask


def get_new_simulations(n=None):
    ts = TemplatedSimulations(base_task=TestTask())
    # create a new sweep for new simulations
    builder = SimulationBuilder()
    builder.add_sweep_definition(JSONConfiguredPythonTask.set_parameter_partial("a"),
                                 [i * i for i in range(100, 120, 3)])
    ts.add_builder(builder=builder)

    new_simulations = ts if n is None else [simulation for simulation in ts.simulations()][0:n]
    return new_simulations


class TestAddingSimulationsToExistingExperiment(unittest.TestCase):

    def setUp(self):
        self.experiment = Experiment.from_task(TestTask())

        # no need to actually run the simulations, just mark them done
        self.experiment.simulations.items.set_status(status=EntityStatus.SUCCEEDED)

    def test_adding_simulations_to_experiment_not_done_should_fail(self) -> None:
        new_simulations = get_new_simulations(n=1)

        # verify starting case
        self.assertTrue(self.experiment.done)

        # make the experiment 'not done'
        self.experiment.add_new_simulations(simulations=new_simulations)

        self.assertRaises(RuntimeError, self.experiment.add_new_simulations, **{'simulations': [new_simulations]})

    def test_adding_non_builder_simulations_should_work(self) -> None:
        new_simulations = get_new_simulations(n=1)

        # add the new simulation and keep track of the existing and total simulation lists
        existing_simulations = [simulation for simulation in self.experiment.simulations.items]
        self.experiment.add_new_simulations(simulations=new_simulations)
        self.verify_added_simulations(experiment=self.experiment, existing_simulations=existing_simulations,
                                      simulations_to_add=new_simulations)

    def test_adding_TemplatedSimulations_should_work(self) -> None:
        new_simulations = get_new_simulations()

        # add the new simulations and keep track of the existing and total simulation lists
        existing_simulations = [simulation for simulation in self.experiment.simulations.items]
        simulations_to_add = [simulation for simulation in new_simulations.simulations()]
        self.experiment.add_new_simulations(simulations=new_simulations)

        self.verify_added_simulations(self.experiment, existing_simulations, simulations_to_add)

    def verify_added_simulations(self, experiment, existing_simulations, simulations_to_add):
        # using experiment.simulations.items in here because each iteration over the experiment.simulations object
        # (a ParentIterator) causes all uids to be set to new values...
        all_simulations = [simulation for simulation in experiment.simulations.items]
        existing_uids = [simulation.uid for simulation in existing_simulations]
        added_simulations = [simulation for simulation in all_simulations if simulation.uid not in existing_uids]

        # verify that the correct number of simulations were added
        self.assertEqual(len(existing_simulations) + len(simulations_to_add), len(all_simulations))
        self.assertEqual(len(simulations_to_add), len(added_simulations))

        # verify existing simulations have unchanged status and new simulations are ready to be created by a platform
        for simulation in experiment.simulations.items:
            if simulation.uid in existing_uids:
                self.assertEqual([s for s in existing_simulations if s.uid == simulation.uid][0].status,
                                 simulation.status)
            else:
                self.assertEqual(None, simulation.status)


class TestExperimentStatus(unittest.TestCase):

    def setUp(self):
        self.experiment = Experiment(simulations=get_new_simulations(n=5))

        # # no need to actually run the simulations, just mark them done
        # self.experiment.simulations.items.set_status(status=EntityStatus.SUCCEEDED)

    def set_simulation_statuses_and_check_experiment_status(self, statuses, expected_status):
        self.assertTrue(len(self.experiment.simulations), sum(statuses.values()))
        status_list = itertools.chain(*[count*[status] for status, count in statuses.items()])
        for simulation in self.experiment.simulations:
            simulation.status = next(status_list)
        self.assertEqual(expected_status, self.experiment.status, f'Expected {expected_status}, was {self.experiment.status}, sim statuses: {statuses}')

    def test_status_is_correct(self) -> None:
        #
        # single sim status cases
        #

        # no simulations in exp

        # all sims are CREATED
        expected = EntityStatus.CREATED
        statuses = {EntityStatus.CREATED: 5}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # all sims are RUNNING
        expected = EntityStatus.RUNNING
        statuses = {EntityStatus.RUNNING: 5}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # all sims are SUCCEEDED
        expected = EntityStatus.SUCCEEDED
        statuses = {EntityStatus.SUCCEEDED: 5}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # all sims are FAILED
        expected = EntityStatus.FAILED
        statuses = {EntityStatus.FAILED: 5}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # all sims are None
        expected = None
        statuses = {None: 5}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)


        #
        # 2-way sim status mixes
        #

        # some CREATED, RUNNING
        expected = EntityStatus.RUNNING
        statuses = {EntityStatus.CREATED: 1, EntityStatus.RUNNING: 4}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some CREATED, SUCCEEDED
        expected = EntityStatus.CREATED
        statuses = {EntityStatus.CREATED: 1, EntityStatus.SUCCEEDED: 4}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some CREATED, FAILED
        expected = EntityStatus.FAILED
        statuses = {EntityStatus.CREATED: 1, EntityStatus.FAILED: 4}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some CREATED, None
        expected = EntityStatus.CREATED  # should only exist during commissioning process
        statuses = {EntityStatus.CREATED: 1, None: 4}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # ---

        # some RUNNING, SUCCEEDED
        expected = EntityStatus.RUNNING
        statuses = {EntityStatus.RUNNING: 1, EntityStatus.SUCCEEDED: 4}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some RUNNING, FAILED
        expected = EntityStatus.FAILED
        statuses = {EntityStatus.RUNNING: 1, EntityStatus.FAILED: 4}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some RUNNING, None
        expected = EntityStatus.CREATED  # should only exist during commissioning process
        statuses = {EntityStatus.RUNNING: 1, None: 4}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # ---

        # some SUCCEEDED, FAILED
        expected = EntityStatus.FAILED
        statuses = {EntityStatus.SUCCEEDED: 1, EntityStatus.FAILED: 4}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some SUCCEEDED, None
        expected = EntityStatus.CREATED
        statuses = {EntityStatus.SUCCEEDED: 1, None: 4}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # ---

        # some FAILED, None
        expected = EntityStatus.CREATED
        statuses = {EntityStatus.FAILED: 1, None: 4}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        #
        # 3-way sim status mixes
        #

        # some CREATED, RUNNING, SUCCEEDED
        expected = EntityStatus.RUNNING
        statuses = {EntityStatus.CREATED: 1, EntityStatus.RUNNING: 2, EntityStatus.SUCCEEDED: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some CREATED, RUNNING, FAILED
        expected = EntityStatus.FAILED
        statuses = {EntityStatus.CREATED: 1, EntityStatus.RUNNING: 2, EntityStatus.FAILED: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some CREATED, RUNNING, None
        expected = EntityStatus.CREATED  # should only exist during commissioning process
        statuses = {EntityStatus.CREATED: 1, EntityStatus.RUNNING: 2, None: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # ---

        # some CREATED, SUCCEEDED, FAILED
        expected = EntityStatus.FAILED
        statuses = {EntityStatus.CREATED: 1, EntityStatus.SUCCEEDED: 2, EntityStatus.FAILED: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some CREATED, SUCCEEDED, None
        expected = EntityStatus.CREATED  # should only exist during commissioning process
        statuses = {EntityStatus.CREATED: 1, EntityStatus.SUCCEEDED: 2, None: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # ---

        # some CREATED, FAILED, None
        expected = EntityStatus.CREATED  # should only exist during commissioning process
        statuses = {EntityStatus.CREATED: 1, EntityStatus.FAILED: 2, None: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # ---

        # some RUNNING, SUCCEEDED, FAILED
        expected = EntityStatus.FAILED
        statuses = {EntityStatus.RUNNING: 1, EntityStatus.SUCCEEDED: 2, EntityStatus.FAILED: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some RUNNING, SUCCEEDED, None
        expected = EntityStatus.CREATED  # should only exist during commissioning process
        statuses = {EntityStatus.RUNNING: 1, EntityStatus.SUCCEEDED: 2, None: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # ---

        # some RUNNING, FAILED, None
        expected = EntityStatus.CREATED  # should only exist during commissioning process
        statuses = {EntityStatus.RUNNING: 1, EntityStatus.FAILED: 2, None: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # ---

        # some SUCCEEDED, FAILED, None
        expected = EntityStatus.CREATED
        statuses = {EntityStatus.SUCCEEDED: 1, EntityStatus.FAILED: 2, None: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        #
        # 4-way sim status mixes
        #

        # some CREATED, RUNNING, SUCCEEDED, FAILED
        expected = EntityStatus.FAILED
        statuses = {EntityStatus.CREATED: 1, EntityStatus.RUNNING: 1, EntityStatus.SUCCEEDED: 1, EntityStatus.FAILED: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some CREATED, RUNNING, SUCCEEDED, None
        expected = EntityStatus.CREATED  # should only exist during commissioning process
        statuses = {EntityStatus.CREATED: 1, EntityStatus.RUNNING: 1, EntityStatus.SUCCEEDED: 1, None: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some CREATED, RUNNING, FAILED, None
        expected = EntityStatus.CREATED  # should only exist during commissioning process
        statuses = {EntityStatus.CREATED: 1, EntityStatus.RUNNING: 1, EntityStatus.FAILED: 1, None: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some CREATED, SUCCEEDED, FAILED, None
        expected = EntityStatus.CREATED  # should only exist during commissioning process
        statuses = {EntityStatus.CREATED: 1, EntityStatus.SUCCEEDED: 1, EntityStatus.FAILED: 1, None: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        # some RUNNING, SUCCEEDED, FAILED, None
        expected = EntityStatus.CREATED  # should only exist during commissioning process
        statuses = {EntityStatus.RUNNING: 1, EntityStatus.SUCCEEDED: 1, EntityStatus.FAILED: 1, None: 2}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)

        #
        # 5-way sim status mix
        #

        # some CREATED, RUNNING, SUCCEEDED, FAILED, None
        expected = EntityStatus.CREATED  # should only exist during commissioning process
        statuses = {EntityStatus.CREATED: 1, EntityStatus.RUNNING: 1, EntityStatus.SUCCEEDED: 1, EntityStatus.FAILED: 1,
                    None: 1}
        self.set_simulation_statuses_and_check_experiment_status(statuses=statuses, expected_status=expected)
