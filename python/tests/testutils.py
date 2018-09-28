
import logging
import unittest
from functools import wraps

def log_title(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        hr = "=" * 80
        log = logging.getLogger(f.__qualname__)
        log.info("")
        log.info(hr)
        log.info(" {} ".format(f.__name__))
        log.info(hr)
        log.info("")
        return f(*args, **kwargs)
    return wrapper

def log_level(name, level):
    """Decorator to temporarily change the log level of 'name' to 'level' within this function."""
    def wrap(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            log = logging.getLogger(name)
            original_level = log.getEffectiveLevel()
            log.setLevel(level)
            try:
                return_args = f(*args, **kwargs)
            except:
                raise
            finally:
                log.setLevel(original_level)

            return return_args
        return decorator
    return wrap

class TestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = logging.getLogger(self.__class__.__name__)

    def log_title(self, title):
        hr = "=" * 80
        self.log.info("")
        self.log.info(hr)
        self.log.info(" {} ".format(title))
        self.log.info(hr)
        self.log.info("")
