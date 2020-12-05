import functools
import os
from contextlib import suppress
from logging import getLogger
from typing import TYPE_CHECKING, Dict
from idmtools import IdmConfigParser
from idmtools.assets import AssetCollection
from idmtools.core import TRUTHY_VALUES
from idmtools.registry.hook_specs import function_hook_impl

if TYPE_CHECKING:
    from idmtools.core.interfaces.ientity import IEntity

logger = getLogger(__name__)
user_logger = getLogger('user')


@function_hook_impl
def idmtools_platform_pre_create_item(item: 'IEntity', kwargs):
    from idmtools.entities.experiment import Experiment
    from idmtools.entities.simulation import Simulation
    from idmtools.entities.iworkflow_item import IWorkflowItem
    from idmtools.entities.suite import Suite
    add_to_all_default = kwargs.get('add_git_tags_to_all', 'f')
    add_to_simulations_default = kwargs.get('add_git_tags_to_simulations', 'f')
    add_to_experiments_default = kwargs.get('add_git_tags_to_experiments', 'f')
    add_to_workitems_default = kwargs.get('add_git_tags_to_workitems', 'f')
    add_to_suite_default = kwargs.get('add_git_tags_to_suite', 'f')
    add_to_asset_collection_default = kwargs.get('add_git_tags_to_asset_collection', 'f')
    if IdmConfigParser.get_option("git_tag", "add_to_all", add_to_all_default) in TRUTHY_VALUES or \
            (isinstance(item, Experiment) and IdmConfigParser.get_option("git_tag", "add_to_experiments", add_to_experiments_default) in TRUTHY_VALUES) or \
            (isinstance(item, Simulation) and IdmConfigParser.get_option("git_tag", "add_to_simulations", add_to_simulations_default) in TRUTHY_VALUES) or \
            (isinstance(item, IWorkflowItem) and IdmConfigParser.get_option("git_tag", "add_to_workitems", add_to_workitems_default) in TRUTHY_VALUES) or \
            (isinstance(item, Suite) and IdmConfigParser.get_option("git_tag", "add_to_suite", add_to_suite_default) in TRUTHY_VALUES) or \
            (isinstance(item, AssetCollection) and IdmConfigParser.get_option("git_tag", "add_to_asset_collection", add_to_asset_collection_default) in TRUTHY_VALUES):
        tags = add_details_using_gitpython()
        if not tags:
            tags = add_details_using_pygit()
            user_logger.warning("You need gitpython or pygit2 installed to have this functionality")
        item.tags.update(tags)


@functools.lru_cache(1)
def add_details_using_gitpython():
    result = dict()
    with suppress(ImportError):
        import git
        repo = git.Repo(search_parent_directories=True)
        if repo:
            sha = repo.head.object.hexsha
            result['git_hash'] = sha
            if len(repo.remotes) > 0:
                result['git_url'] = repo.remotes[0].url
            if repo.head.ref.name:
                result['git_branch'] = repo.head.ref.name
    return result


@functools.lru_cache(1)
def add_details_using_pygit() -> Dict[str, str]:
    result = dict()
    with suppress(ImportError):
        import pygit2
        repo_base = pygit2.discover_repository(os.getcwd())
        if repo_base:
            repo = pygit2.Repository(repo_base)
            sha = repo.head.target.hex
            result['git_hash'] = sha
            if len(repo.remotes) > 0:
                result['git_url'] = repo.remotes[0].url
            if repo.head.shorthand:
                result['git_branch'] = repo.head.shorthand
    return result
