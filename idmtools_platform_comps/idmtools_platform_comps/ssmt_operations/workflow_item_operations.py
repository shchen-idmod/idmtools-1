from dataclasses import dataclass
from typing import List, Dict

from idmtools.entities.simulation import Simulation
from idmtools_platform_comps.comps_operations.workflow_item_operations import CompsPlatformWorkflowItemOperations


@dataclass
class SSMTPlatformWorkflowItemOperations(CompsPlatformWorkflowItemOperations):
    def get_assets(self, simulation: Simulation, files: List[str], **kwargs) -> Dict[str, bytearray]:
        raise NotImplementedError("Fetching files for simulation is not currently implemented for SSMT")