import functools
import inspect
from logging import DEBUG
from typing import Type, List, Any, Set

import pluggy

from idmtools.core.registry.PluginSpecification import PluginSpecification, PLUGIN_REFERENCE_NAME, logger, list_rindex


def is_a_plugin_of_type(value, plugin_specification: Type[PluginSpecification]) -> bool:
    """
    Determine if a value if a plugin specification of type plugin_specification

    Args:
        value: Value to inspect
        plugin_specification: Plugin specification to check against

    Returns:
        (bool) True if the plugin is of a subclass of PluginSpecification, else False
    """
    return inspect.isclass(value) and issubclass(value, plugin_specification) \
        and not inspect.isabstract(value) and value is not plugin_specification


def plugins_loader(entry_points_name: str, plugin_specification: Type[PluginSpecification]) -> Set[PluginSpecification]:
    """
    Loads all the plugins of type *plugin_specification* from entry-point name. We also support loading plugins
    through a list of strs representing the paths to modules containing plugins

    Args:
        entry_points_name: Entry point name for plugins
        plugin_specification: Plugin specification to load

    Returns:
        (Set[PluginSpecification]): All the plugins of type X
    """
    manager = pluggy.PluginManager(PLUGIN_REFERENCE_NAME)
    manager.add_hookspecs(plugin_specification)
    manager.load_setuptools_entrypoints(entry_points_name)

    manager.check_pending()
    return manager.get_plugins()


@functools.lru_cache(maxsize=32)
def discover_plugins_from(library: Any, plugin_specification: Type[PluginSpecification]) -> \
        List[Type[PluginSpecification]]:
    """
    Search a library obj for plugins of type plugin_specification.

    Currently it detects module and classes. In the future support for strs will be added
    Args:
        library: Library object to discover plugins from
        plugin_specification: Specification to search for

    Returns:
        List[Type[PluginSpecification]]: List of Plugins
    """

    plugins = []
    # check if the item is a module
    if inspect.ismodule(library):
        if logger.isEnabledFor(DEBUG):
            logger.debug('Attempting to load library as a module: %s', library.__name__)
        for k, v in library.__dict__.items():
            if k[:2] != '__' and is_a_plugin_of_type(v, plugin_specification):
                if logger.isEnabledFor(DEBUG):
                    logger.debug('Adding class %s from %s as a plugin', v.__name__, library.__name__)
                plugins.append(v)
    # or maybe a plugin object
    elif is_a_plugin_of_type(library, plugin_specification):
        if logger.isEnabledFor(DEBUG):
            logger.debug('Adding class %s as a plugin', library.__name__)
        plugins.append(library)
    else:
        logger.warn('Could not determine the the type of library specified by %s', str(library))
    return plugins