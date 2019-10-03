from COMPS import Data
from COMPS.Data import QueryCriteria, Simulation as COMPSSimulation


def get_asset_collection_id_for_simulation_id(sim_id):
    # query_criteria = QueryCriteria().select_children('configuration')
    # simulation = Simulation.get(id=sim_id, query_criteria=query_criteria)

    # Temporary stand-in for pycomps fix; code below from Jeff S. Replace with above code
    # once new pycomps version is available.
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
    simulation = COMPSSimulation.get(sim_id, query_criteria=QueryCriteriaExt().select(
        ['id', 'experiment_id']).select_children(
        ["files", "configuration"]).add_extra_params({'coalesceconfig': True}))

    collection_id = simulation.configuration.asset_collection_id
    return collection_id


def get_asset_collection_by_id(collection_id, query_criteria=None):
    query_criteria = query_criteria or QueryCriteria().select_children('assets')
    try:
        return Data.AssetCollection.get(collection_id, query_criteria)
    except (RuntimeError, ValueError):
        return None
