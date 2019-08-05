import os
import platform
import time
import unittest
from functools import wraps
from typing import Callable

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
comps_test = unittest.skipIf(
    not os.environ.get('COMPS_TESTS', False), 'No COMPS testing'
)

docker_test = unittest.skipIf(
    not os.environ.get('DOCKER_TESTS', False), 'No Docker testing'
)

linux_only = unittest.skipIf(
    not platform.system() in ["Linux", "Darwin"], 'No Tests that are meant for linux'
)


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
