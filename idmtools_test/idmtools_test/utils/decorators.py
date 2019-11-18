import os
import platform
import time
import unittest
from functools import wraps
from typing import Callable
import docker
# The following decorators are used to control test
# To allow for different use cases(dev, test, packaging, etc)
# We have switches that should allow a rich set of possible
# test combinations
#
# The default tests run with all the optional tests set to off(except Linux since that is auto-detected)
# For test-external runs any tests that require external communication
# This currently is any comps related test
# test-docker run any tests that depend on docker locally(Mostly local runn)
# test-all runs all tests

linux_only = unittest.skipIf(
    not platform.system() in ["Linux", "Darwin"], 'No Tests that are meant for linux'
)

windows_only = unittest.skipIf(
    platform.system() in ["Linux", "Darwin"], 'No Tests that are meant for Windows'
)

# this is mainly for docker in docker environments but also applies to environments
# where you must use the local ip address for connectivity vs localhost
skip_api_host = unittest.skipIf(os.getenv("API_HOST", None) is not None, "API_HOST is defined")
client = docker.from_env()


def run_test_in_n_seconds(n: int, print_elapsed_time: bool = False) -> Callable:
    """
    Decorator that assert a test will run in N seconds. If it does not, it will fail.

    THIS DOES NOT MANAGE processes and it will not stop long running processes. It simply times a test and ensure it
    ran in less than N seconds

    Args:
        n (int): Number of seconds that is considered acceptable
        print_elapsed_time: Will print the function name and elasped time at the end of each function it decorates

    Returns:
        (Callable) : Wrapped function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            ret = func(*args, **kwargs)
            end = time.time()
            if print_elapsed_time:
                print(f"{func.__name__} took {end - start}s to run!")
            args[0].assertLess(end - start, n, f"{func.__name__} took {end - start}s to run!")
            return ret

        return wrapper

    return decorator


def restart_local_platform(silent=True, stop_before=True, stop_after=True, dump_logs=True, *args, **kwargs):
    from idmtools_platform_local.infrastructure.service_manager import DockerServiceManager
    from idmtools_platform_local.infrastructure.docker_io import DockerIO
    from idmtools_platform_local.cli.utils import get_service_info
    # disable spinner
    if silent:
        os.environ['NO_SPINNER'] = '1'

    args = (client, ) + args
    sm = DockerServiceManager(*args, **kwargs)
    do = DockerIO()

    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if stop_before:
                sm.cleanup(tear_down_brokers=True, delete_data=True)
                do.cleanup(True)
            result = None
            try:
                result = func(*args, **kwargs)
            except Exception:
                raise
            finally:
                if dump_logs:
                    try:
                        info = get_service_info(sm, diff=False, logs=True)
                        print(info)
                    except:
                        pass
                if stop_after:
                    sm.cleanup(tear_down_brokers=True, delete_data=True)
                    do.cleanup(True)
            return result
        return wrapper
    return decorate