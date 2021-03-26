import time
import logging
from functools import wraps
LOGGER = logging.getLogger(__name__)


def log_latency_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        LOGGER.info(f"\nRunning {func.__name__}.")
        start_time = time.time()
        LOGGER.info(f"Start time is {start_time}.")
        res = func(*args, **kwargs)
        end_time = time.time()
        LOGGER.info(f"End time is {end_time}.")
        LOGGER.info(f"Total time taken in seconds is {end_time - start_time}.")
        return res
    return wrapper