import itertools
import traceback
import typing

from idmtools.utils.file_parser import FileParser
from typing import NoReturn

if typing.TYPE_CHECKING:
    from idmtools.entities.iplatform import TPlatform
    from idmtools.entities.iitem import TItem
    from idmtools.entities.ianalyzer import TAnalyzerList
    from diskcache import Cache


def map_item(item: 'TItem') -> NoReturn:
    """
    A worker process entry point for analyzer item-mapping that initializes some worker-global values

    Args:
        item: The item (often simulation) to process

    Returns:
    """
    # Retrieve the global variables coming from the pool initialization
    analyzers = map_item.analyzers
    cache = map_item.cache
    platform = map_item.platform

    _get_mapped_data_for_item(item, analyzers, cache, platform)


def _get_mapped_data_for_item(item: 'TItem', analyzers: 'TAnalyzerList', cache: 'Cache', platform: 'TPlatform') -> bool:
    """

    Args:
        item: the IItem object to call analyzer map() methods on
        analyzers: IAnalyzer items with map() methods to call on the provided items
        cache: The diskcache Cache object to store item map() results in
        platform: a platform object to query for information

    Returns: False if an exception occurred, else True (succeeded)

    """
    # determine which analyzers (and by extension, which filenames) are applicable to this item
    try:
        analyzers_to_use = [a for a in analyzers if a.filter(item)]
    except Exception:
        analyzer_uids = [a.uid for a in analyzers]
        _set_exception(step="Item filtering",
                       info={"Item": item, "Analyzers": ", ".join(analyzer_uids)},
                       cache=cache)

    filenames = set(itertools.chain(*(a.filenames for a in analyzers_to_use)))

    # The byte_arrays will associate filename with content
    try:
        file_data = platform.get_files(item, filenames)  # make sure this does NOT error when filenames is empty
    except Exception:
        # an error has occurred
        analyzer_uids = [a.uid for a in analyzers]
        _set_exception(step="data retrieval",
                       info={"Item": item, "Analyzers": ", ".join(analyzer_uids), "Files": ", ".join(filenames)},
                       cache=cache)
        return False

    # Selected data will be a dict with analyzer.uid: data  entries
    selected_data = {}
    for analyzer in analyzers_to_use:
        # If the analyzer needs the parsed data, parse
        if analyzer.parse:
            try:
                data = {filename: FileParser.parse(filename, content)
                        for filename, content in file_data.items()}
            except Exception:
                _set_exception(step="data parsing",
                               info={"Item": item, "Analyzer": analyzer.uid},
                               cache=cache)
                return False
        else:
            # If the analyzer doesnt wish to parse, give the raw data
            data = file_data

        # run the mapping routine for this analyzer and item
        try:
            selected_data[analyzer.uid] = analyzer.map(data, item)
        except Exception:
            _set_exception(step="data processing", info={"Item": item, "Analyzer": analyzer.uid},
                           cache=cache)
            return False

    # Store all analyzer results for this item in the result cache
    cache.set(item.uid, selected_data)
    return True


def _set_exception(step: str, info: dict, cache: 'Cache') -> NoReturn:
    """
    Sets an exception in the cache in a standardized way.

    Args:
        step: Which step encountered an error
        info: Dictionary for additional information to add to the message
        cache: The cache object in which to set the exception

    Returns:

    """
    from idmtools_core.idmtools.analysis.AnalyzeManager import AnalyzeManager

    # construct exception message including traceback
    message = f'\nAn exception has been raised during {step}.\n'
    for key, value in info.items():
        message += f'- {key}: {value}\n'
    message += f'\n{traceback.format_exc()}\n'

    cache.set(AnalyzeManager.EXCEPTION_KEY, message)
