import json
from enum import Enum
from json import JSONEncoder
from logging import getLogger
from typing import List, Any, Dict, Union
from uuid import UUID
from idmtools.assets import AssetCollection, Asset
from idmtools.core import EntityStatus
from idmtools.entities import CommandLine
from idmtools.entities.experiment import Experiment
from idmtools.entities.itask import ITask
from idmtools.entities.simulation import Simulation
from idmtools.utils.entities import as_dict
from datetime import datetime

user_logger = getLogger('user')


class DefaultEncoder(JSONEncoder):
    """
    A default JSON encoder to naively make Python objects serializable by using their __dict__.
    """

    def default(self, o):
        return o.__dict__


class IDMJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            return o.value
        elif isinstance(o, EntityStatus):
            return o.value
        elif isinstance(o, Experiment):
            return o.to_dict()
        elif isinstance(o, Simulation):
            return o.to_dict()
        elif isinstance(o, ITask):
            result = o.to_dict()
            result["task_type"] = o.__class__.__name__
            return result
        elif isinstance(o, bytes):
            return None
        elif isinstance(o, (CommandLine, UUID)):
            return str(o)
        elif isinstance(o, Asset):
            return as_dict(o, exclude=['content'])
        elif isinstance(o, AssetCollection):
            return o.assets
        elif isinstance(o, (dict, int, list, str)):
            return o
        elif isinstance(o, datetime):
            return str(o)


def load_json_file(path: str) -> Union[Dict[Any, Any], List]:
    """
    Load a json object from a file

    Args:
        path: Path to file

    Returns:
        Contents of file parsed by JSON
    """
    if not path:
        return
    try:
        with open(path, 'r') as fp:
            return json.load(fp)
    except IOError as e:
        user_logger.error(f"The file at {path} could not be loaded or parsed to JSON.\n{e}")
