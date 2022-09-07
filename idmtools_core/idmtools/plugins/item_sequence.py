"""
Defines a id generator plugin that generates ids in sequence by item type.
To configure, set 'id_generator' in .ini configuration file to 'item_sequence':
[COMMON]
id_generator = item_sequence

You can also customize the sequence_file that stores the sequential ids per item type
as well as the id format using the following parameters in the .ini configuration file:
[item_sequence]
sequence_file = <file_name>.json    ex: item_sequences.json
id_format_str = <custom_str_format>     ex: {item_name}{data[item_name]:06d}

Copyright 2021, Bill & Melinda Gates Foundation. All rights reserved.
"""
import json
import time
from functools import cache
from json import JSONDecodeError
from logging import getLogger, INFO, DEBUG
from pathlib import Path
from random import randint

import jinja2
from filelock import FileLock
from jinja2 import environment

from idmtools import IdmConfigParser
from idmtools.core.interfaces.ientity import IEntity
from idmtools.registry.hook_specs import function_hook_impl

logger = getLogger(__name__)


def load_existing_sequence_data(sequence_file):
    """
    Loads item sequence data from sequence_file into a dictionary.

    Args:
        sequence_file: File that user has indicated to store the sequential ids of items

    Returns:
        Data loaded from sequence_file as a dictionary
    """
    data = dict()

    if Path(sequence_file).exists():
        with open(sequence_file, 'r') as file:
            try:
                data = json.load(file)
            except JSONDecodeError:
                return dict()
    return data


@cache
def get_plugin_config():
    """
    Retrieves the sequence file and format string (for id generation) from the .ini config file.

    Returns:
        sequence_file: specified json file in .ini config in which id generator keeps track of sequential id's
        id_format_str: string specified in .ini config by which id's are formatted when assigned to sequential items
    """
    sequence_file = Path(IdmConfigParser.get_option("item_sequence", "sequence_file", 'item_sequences.json')).expanduser()
    id_format_str = IdmConfigParser.get_option("item_sequence", "id_format_str", None)
    return sequence_file, id_format_str


@cache
def _get_template(id_format_str):
    """
    Get our jinja template. Cache this to reduce work
    Args:
        id_format_str: Format string

    Returns:
        Jinja2 template
    """
    environment = jinja2.Environment()
    template = environment.from_string(id_format_str)
    return template


@function_hook_impl
def idmtools_generate_id(item: IEntity) -> str:
    """
    Generates a UUID.

    Args:
        item: IEntity using the item_sequence plugin

    Returns:
        ID for the respective item, based on the formatting defined in the id_format_str (in .ini config file)

    """
    sequence_file, id_format_str = get_plugin_config()
    # we can check for existence here since it should only not exist when a new sequence is started
    if not sequence_file.parent.exists():
        if logger.isEnabledFor(INFO):
            logger.info(f"Creating {sequence_file.parent}")
        sequence_file.parent.mkdir(exist_ok=True, parents=True)

    max_tries = 100
    attempts = 0
    data = dict()
    item_name = str(item.item_type if hasattr(item, 'item_type') else "Unknown")
    while attempts < max_tries:
        try:
            lock = FileLock(f"{sequence_file}.lock", timeout=1)
            with lock:
                data = load_existing_sequence_data(sequence_file)

                if item_name in data:
                    data[item_name] += 1
                else:
                    if logger.isEnabledFor(INFO):
                        logger.info(f"Starting sequence for {item_name} at 0")
                    data[item_name] = 0

                with open(sequence_file, 'w') as f:
                    json.dump(data, f)
                break
        except Exception as e:
            attempts += 1
            if attempts >= max_tries:
                raise e
            # We had an issue generating sequence. We assume
            if logger.isEnabledFor(DEBUG):
                logger.error("Trouble generating sequence.")
                logger.exception(e)
            time.sleep(randint(1, 4) * 0.01)
    if id_format_str:
        return _get_template(id_format_str).render(**locals())
    else:
        return f'{item_name}{data[item_name]:07d}'
