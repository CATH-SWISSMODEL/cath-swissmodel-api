"""
Common classes and helpers for CLI interaction
"""

# core
import argparse
import json
import logging
import os

# non-core
import getpass

# local
from cathsm.apiclient.config import ApiConfig

LOG = logging.getLogger(__name__)

class ApiArgumentParser(argparse.ArgumentParser):
    """
    Defines standard CLI options for API clients (and sets up logging)
    """

    def __init__(self, *args, **kwargs):

        if 'description' not in kwargs:
            raise Exception("require 'description' field")

        super().__init__(**kwargs)

        self.add_argument('--in',
                          type=str, required=True, dest='infile', 
                          help='input data file')
        self.add_argument('--out',
                          type=str, required=True, dest='outfile', 
                          help='output results file')
        self.add_argument('--delete-config',
                          action='store_true', dest='clear_config',
                          help='remove settings from the config file',
                          default=False)
        self.add_argument('--user',
                          type=str, required=False, dest='api_user', 
                          help='specify API user')
        self.add_argument('--pass',
                          type=str, required=False, dest='api_password', 
                          help='specify API password')
        self.add_argument('--token',
                          type=str, required=False, dest='api_token',
                          help='specify API token')
        self.add_argument('--sleep',
                          type=int, default=5, 
                          help='waiting time between requests')
        self.add_argument('-v', '--verbose',
                          action="store_true",
                          help='increase output verbosity')
        self.add_argument('-q', '--quiet',
                          action="store_true",
                          help='decrease output verbosity')

    def parse_args(self):

        args = super().parse_args()

        # Get API token. Order: arg, env, config
        if not args.api_token:
            args.api_token = self._get_env('API_TOKEN')

        if not args.api_token:
            # We need a username and password
            if not args.api_user:
                args.api_user = self._get_env('API_USER')
            if not args.api_user:
                args.api_user = LazyFun(lambda: input("Username: "))

            if not args.api_password:
                args.api_password = self._get_env('API_PASSWORD')
            if not args.api_password:
                args.api_password = LazyFun(getpass.getpass)

        return args

    def _get_env(self, envkey, default=None):
        var = None
        if envkey in os.environ:
            var = os.environ[envkey]
        else:
            var = default
        return var


class LazyFun(object):
    """
    Lazy evaluation of function returning a string
    """
    def __init__(self, fun):
        self.fun = fun
        self._evaluated = False

    def __str__(self):
        if not self._evaluated:
            self._string = self.fun()
        return self._string

