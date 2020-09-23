import os

from COMPS import Data
from COMPS.Data import AssetCollection as CompsAssetCollection
from COMPS.Data import QueryCriteria, Simulation as COMPSSimulation, Experiment as COMPSExperiment
from idmtools.builders import SimulationBuilder
from idmtools.core.enums import EntityStatus
from idmtools.entities.experiment import Experiment


def get_asset_collection_id_for_simulation_id(sim_id):
    """
    Obtains COMPS AssetCollection id from a given simulation id.
    :param sim_id: A simulation id to retrieve assetcollection id from
    :return: COMPS AssetCollection id
    """
    simulation = COMPSSimulation.get(sim_id, query_criteria=QueryCriteria().select(
        ['id', 'experiment_id']).select_children(
        ["files", "configuration"]))

    if simulation.configuration is None:
        # check experiment
        experiment = COMPSExperiment.get(simulation.experiment_id, query_criteria=QueryCriteria().select(
            ['id']).select_children("configuration")
        )
        collection_id = experiment.configuration.asset_collection_id
    else:
        collection_id = simulation.configuration.asset_collection_id
    return collection_id


def get_asset_collection_by_id(collection_id, query_criteria=None) -> CompsAssetCollection:
    """
    Obtains COMPS AssetCollection from a given collection id.
    :param collection_id: An asset collection id to retrieve assetcollection from
    :param query_criteria: query_criteria
    :return: COMPS AssetCollection
    """
    query_criteria = query_criteria or QueryCriteria().select_children('assets')
    try:
        return Data.AssetCollection.get(collection_id, query_criteria)
    except (RuntimeError, ValueError):
        return None


def sims_from_experiment(e):
    o = e
    if isinstance(e, Experiment):
        o = e.get_platform_object()
    return o.get_simulations(QueryCriteria().select(['id', 'state']).select_children('hpc_jobs'))


def workdirs_from_simulations(sims):
    return {str(sim.id): sim.hpc_jobs[-1].working_directory for sim in sims if sim.hpc_jobs}


def get_simulation_path(simulation):
    path = workdirs_from_simulations([simulation])[str(simulation.id)]
    return path


def get_simulation_by_id(sim_id, query_criteria=None):
    return COMPSSimulation.get(id=sim_id, query_criteria=query_criteria)


def assure_running_then_wait_til_done(tst, experiment):
    tst.platform.run_items(items=[experiment])
    tst.platform.refresh_status(item=experiment)
    tst.assertFalse(experiment.done)
    tst.assertTrue(all([s.status == EntityStatus.RUNNING for s in experiment.simulations]))
    # Wait till done
    import time
    start_time = time.time()
    while time.time() - start_time < 180:
        tst.platform.refresh_status(item=experiment)
        if experiment.done:
            break
        time.sleep(3)
    tst.assertTrue(experiment.done)


def setup_test_with_platform_and_simple_sweep(tst):
    from idmtools.core.platform_factory import Platform
    tst.platform = Platform('SLURM')
    print(tst.case_name)

    def setP(simulation, p):
        return simulation.task.set_parameter("P", p)

    tst.builder = SimulationBuilder()
    tst.builder.add_sweep_definition(setP, [1, 2, 3])
