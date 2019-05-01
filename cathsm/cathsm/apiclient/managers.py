"""
Clients that provide interaction with CATH / SWISS-MODEL API.
"""

# core
import logging
import sys
import time

# local
from cathsm.apiclient.models import SubmitAlignment, SubmitSelectTemplate
from cathsm.apiclient.cli import ApiArgumentParser, ApiConfig
from cathsm.apiclient.errors import AuthenticationError, ArgError
from cathsm.apiclient.clients import (SMAlignmentApiClient,
    CathSelectTemplateApiClient)

DEFAULT_INFO_FORMAT = '%(asctime)s %(levelname)7s | %(message)s'
DEFAULT_DEBUG_FORMAT = '%(asctime)s %(name)-30s %(levelname)7s | %(message)s'
LOG = logging.getLogger(__name__)


class ApiClientManagerBase(object):

    def __init__(self, *, infile, outfile, 
                 sleep=5, log_level=logging.INFO,
                 api_user=None, api_password=None, api_token=None,
                 config=None, config_section=None, clear_config=False):
        
        if not config_section:
            config_section=self.__class__.__name__      

        if config is None:
            config = ApiConfig(section=config_section)
        else:
            config.section = config_section
        
        if clear_config:
            LOG.info("Clearing existing config for section: '{}'".format(config.section))
            config.delete_section()

        self.infile = infile
        self.outfile = outfile
        self.sleep = sleep
        self.log_level = log_level

        self.api_token = api_token
        self.api_user = api_user
        self.api_password = api_password

        if not self.api_token:
            if 'api_token' in config:
                self.api_token = config['api_token']
            elif self.api_user and self.api_password:
                pass
            else:
                raise ArgError("expected 'api_token' or ('api_user' and 'api_password')")

        self._config = config

    @classmethod
    def new_from_cli(cls, *, parser=None):
        if not parser:
            parser = ApiArgumentParser(description=cls.__doc__)
        args = parser.parse_args()

        level=logging.INFO
        if args.verbose:
            level=logging.DEBUG
        if args.quiet:
            level=logging.WARNING
        cls.addLogger(level=level)

        passthrough_args = ('infile', 'outfile', 'sleep', 'clear_config',
            'api_token', 'api_user', 'api_password')

        kwargs = {k: v for k, v in vars(args).items() if k in passthrough_args}

        LOG.debug("Passing CLI args: {}".format(kwargs))

        return cls(**kwargs)

    @classmethod
    def addLogger(cls, *, level=logging.INFO, logger=None, handler=None, formatter=None):

        if not formatter:
            if level <= logging.DEBUG:
                log_format = DEFAULT_DEBUG_FORMAT 
            elif level >= logging.INFO:
                log_format = DEFAULT_INFO_FORMAT
            formatter = logging.Formatter(log_format)

        if not handler:
            handler = logging.StreamHandler()

        if not logger:
            logger = logging.getLogger()

        logger.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    def authenticate(self):

        api = self._apiclient
        config = self._config

        if self.api_token is not None:
            LOG.info("Setting API token ... ")
            api.set_token(api_token=self.api_token)
        else:
            LOG.info("Authenticating via user/pass... (token_id not provided) ")
            api_token = api.authenticate(api_user=self.api_user, api_pass=self.api_password)
            LOG.debug("Saving API token to config file")
            config['api_token'] = api_token


class CathSelectTemplateApiClientManager(ApiClientManagerBase):
    """
    Selected template structure from sequence (via CATH API)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self._apiclient = CathSelectTemplateApiClient()
        self._submit_data_cls = SubmitSelectTemplate

    def run(self):
    
        api = self._apiclient
        config = self._config

        LOG.info("IN_FILE:  {}".format(self.infile))
        LOG.info("OUT_FILE: {}".format(self.outfile))

        self.authenticate()

        LOG.info("Loading data from file '%s' ...", self.infile)
        with open(self.infile) as infile:
            submit_data = SubmitSelectTemplate.load(infile)

        LOG.info("Submitting data ... ")
        submit_r = api.submit(data=submit_data)
        LOG.info("Response: %s", submit_r)
        task_id = submit_r['uuid']
        
        LOG.info("Checking status of task <{}> ...".format(task_id))
        while True:
            status_r = api.status(task_id)
            status = status_r['status'].upper()
            LOG.info("   status: %s", status)
            if status == 'SUCCESS':
                break
            if status == 'ERROR':
                LOG.error("Sequence search failed: %s", status_r['message'])
                sys.exit(1)
            else:
                time.sleep(self.sleep)

        LOG.info("Retrieving results ... ")
        result_r = api.results(task_id)
        
        result_r['results_json']

        LOG.info("result: {}".format(result_r))
        
        LOG.info("Writing resolved hits to {}".format(self.outfile))
        with open(self.outfile, 'w') as outfile:
            outfile.write()

class SMAlignmentApiClientManager(ApiClientManagerBase):
    """
    Generates 3D model from alignment data (via SWISS-MODEL API)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self._apiclient = SMAlignmentApiClient()

    def run(self):
    
        api = self._apiclient
        config = self._config

        LOG.info("IN_FILE:  {}".format(self.infile))
        LOG.info("OUT_FILE: {}".format(self.outfile))

        self.authenticate()

        LOG.info("Loading data from file '%s' ...", self.infile)
        with open(self.infile) as infile:
            submit_data = SubmitAlignment.load(infile)

        LOG.info("Submitting data ... ")
        submit_r = api.submit(data=submit_data)
        project_id = submit_r['project_id']
        
        LOG.info("Checking status of project <{}> ...".format(project_id))
        while True:
            status_r = api.status(project_id)
            status = status_r['status']
            LOG.info("   status: %s", status)
            if status == 'COMPLETED':
                break
            if status == 'FAILED':
                LOG.error("Modelling failed: " + status_r['message'])
                sys.exit(1)
            else:
                time.sleep(self.sleep)

        LOG.info("Retrieving results ... ")
        result_r = api.results(project_id)
        
        def truncate_strings(s):
            if type(s) == str and len(s) > 100:
                s = str(s[:100] + '...')
            return s

        truncated_result = {k: truncate_strings(v) for k, v in result_r.items()}
        LOG.debug("result: {}".format(truncated_result))
        coords = result_r['coordinates']
        
        LOG.info("Writing coordinates to {}".format(self.outfile))
        with open(self.outfile, 'w') as outfile:
            outfile.write(coords)

