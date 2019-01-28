"""
Common classes and helpers for CLI interaction
"""

# core
import argparse
import logging
import os

DEFAULT_API_USER = 'junk@sillit.com'
DEFAULT_API_PASSWORD = 'FJRbnz'

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
        self.add_argument('--user', 
                          type=str, required=False, dest='api_user', 
                          help='specify API user')
        self.add_argument('--pass',
                          type=str, required=False, dest='api_password', 
                          help='specify API password')
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

        if not args.api_user:
            args.api_user = self._get_env('API_USER', DEFAULT_API_USER)

        if not args.api_password:
            args.api_password = self._get_env('API_PASSWORD', DEFAULT_API_PASSWORD)

        return args

    def _get_env(self, envkey, default=None):
        var = None
        if envkey in os.environ:
            var = os.environ[envkey]
        else:
            var = default
        return var

