from dataclasses import field, dataclass
from inspect import signature
from logging import getLogger, DEBUG
from typing import List, Callable, TYPE_CHECKING, NoReturn
from abc import ABCMeta
from idmtools.core import EntityStatus
from idmtools.core.interfaces.ientity import IEntity

if TYPE_CHECKING:  # pragma: no cover
    from idmtools.entities.iplatform import IPlatform

runnable_hook = Callable[['IRunnableEntity', 'IPlatform'], None]
logger = getLogger(__name__)


@dataclass
class IRunnableEntity(IEntity, metaclass=ABCMeta):
    __pre_run_hooks: List[runnable_hook] = field(default_factory=list, metadata={"md": True})
    __post_run_hooks: List[runnable_hook] = field(default_factory=list, metadata={"md": True})

    def pre_run(self, platform: 'IPlatform') -> None:
        """
        Called before the actual creation of the entity.

        Args:
            platform: Platform item is being created on

        Returns:

        """

        for hook in self.__pre_run_hooks:
            if logger.isEnabledFor(DEBUG):
                logger.debug(f'Calling pre-create hook named {hook.__name__ if hasattr(hook, "__name__") else str(hook)}')
            hook(self, platform)

    def post_run(self, platform: 'IPlatform') -> None:
        """
        Called after the actual creation of the entity.

        Args:
            platform: Platform item was created on

        Returns:

        """
        for hook in self.__post_run_hooks:
            if logger.isEnabledFor(DEBUG):
                logger.debug(f'Calling pre-create hook named {hook.__name__ if hasattr(hook, "__name__") else str(hook)}')
            hook(self, platform)

    def add_pre_run_hook(self, hook: runnable_hook):
        """
        Adds a hook function to be called before an item is ran

        Args:
            hook: Hook function. This should have two arguments, the item and the platform

        Returns:
            None
        """
        if len(signature(hook).parameters) != 2:
            raise ValueError("Pre Run hooks should have 2 arguments. The first argument will be the item, the second the platform")
        self.__pre_run_hooks.append(hook)

    def add_post_run_hook(self, hook: runnable_hook):
        """
        Adds a hook function to be called after an item has ran

        Args:
            hook: Hook function. This should have two arguments, the item and the platform

        Returns:
            None
        """
        if len(signature(hook).parameters) != 2:
            raise ValueError("Post Run hooks should have 2 arguments. The first argument will be the item, the second the platform")
        self.__post_run_hooks.append(hook)

    def run(self, wait_until_done: bool = False, platform: 'IPlatform' = None, wait_on_done_progress: bool = True, wait_on_done: bool = True, **run_opts) -> NoReturn:
        """
        Runs an item

        Args:
            wait_until_done: Whether we should wait on item to finish running as well. Defaults to False
            platform: Platform object to use. If not specified, we first check object for platform object then the current context
            wait_on_done_progress: Defaults to true
            **run_opts: Options to pass to the platform

        Returns:
            None
        """
        p = super()._check_for_platform_from_context(platform)
        p.run_items(self, wait_on_done_progress=wait_on_done_progress, **run_opts)
        if wait_until_done or wait_on_done:
            self.wait(wait_on_done_progress=wait_on_done_progress, platform=p)

    def wait(self, wait_on_done_progress: bool = True, timeout: int = None, refresh_interval=None, platform: 'IPlatform' = None, **kwargs):
        """
        Wait on an item to finish running

        Args:
            wait_on_done_progress: Should we show progress as we wait?
            timeout: Timeout to wait
            refresh_interval: How often to refresh object
            platform: Platform. If not specified, we try to determine this from context

        Returns:

        """
        # If done, exit
        if self.status in [EntityStatus.SUCCEEDED, EntityStatus.FAILED]:
            return
        if self.status not in [EntityStatus.CREATED, EntityStatus.RUNNING]:
            raise ValueError("The item cannot be waited for if it is not in Running/Created state")
        opts = dict(**kwargs)
        if timeout:
            opts['timeout'] = timeout
        if refresh_interval:
            opts['refresh_interval'] = refresh_interval
        p = super()._check_for_platform_from_context(platform)
        if wait_on_done_progress:
            p.wait_till_done_progress(self, **opts)
        else:
            p.wait_till_done(self, **opts)
