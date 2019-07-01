"""
Clients that provide interaction with CATH / SWISS-MODEL API.
"""

# core
import logging
import getpass
import sys
import time

# local
from cathsm.apiclient.models import SubmitAlignment, SubmitSelectTemplate
from cathsm.apiclient.cli import ApiArgumentParser, ApiConfig
from cathsm.apiclient.errors import ArgError, NoResultsError
from cathsm.apiclient import clients

DEFAULT_INFO_FORMAT = '%(asctime)s %(levelname)7s | %(message)s'
DEFAULT_DEBUG_FORMAT = '%(asctime)s %(name)-30s %(levelname)7s | %(message)s'
LOG = logging.getLogger(__name__)


class ApiClientManagerBase(object):

    def __init__(self, *, api_client,
                 sleep=5, log_level=logging.INFO,
                 infile=None, outfile=None, submit_data=None,
                 api_user=None, api_password=None, api_token=None,
                 config=None, config_section=None, clear_config=False,
                 logger=None):

        if not logger:
            logger = LOG

        self.log = logger

        if not config_section:
            config_section = self.__class__.__name__

        if config is None:
            config = ApiConfig(section=config_section)
        else:
            config.section = config_section

        if clear_config:
            self.log.info(
                "Clearing existing config for section: '%s'", config.section)
            config.delete_section()

        self.infile = infile
        self.outfile = outfile
        self.submit_data = submit_data
        self.sleep = sleep
        self.log_level = log_level

        self.api_token = api_token
        self.api_user = api_user
        self.api_password = api_password

        self.api_client = api_client

        if not self.api_token:
            if self.api_user and self.api_password:
                pass
            elif 'api_token' in config:
                self.api_token = config['api_token']
            elif self.api_user:
                LOG.info("Please specify password (user={}): {}".format(
                    self.api_user, self.api_client.base_url))
                self.api_password = getpass.getpass()
            else:
                raise ArgError(
                    "expected 'api_token' or 'api_user'")

        self._config = config

    @classmethod
    def new_from_cli(cls, *, parser=None):
        if not parser:
            parser = ApiArgumentParser(description=cls.__doc__)
        args = parser.parse_args()

        level = logging.INFO
        if args.verbose:
            level = logging.DEBUG
        if args.quiet:
            level = logging.WARNING
        cls.addLogger(level=level)

        passthrough_args = ('infile', 'outfile', 'submit_data', 'sleep', 'clear_config',
                            'api_token', 'api_user', 'api_password')

        kwargs = {k: v for k, v in vars(args).items() if k in passthrough_args}

        LOG.debug("Passing CLI args: %s", kwargs)

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

        api = self.api_client
        config = self._config

        if self.api_token is not None:
            self.log.info("Setting API token ... ")
            api_token = self.api_token
        else:
            self.log.info(
                "Authenticating via user/pass... (token_id not provided) ")
            self.log.debug("user: %s", self.api_user)
            api_token = api.authenticate(
                api_user=self.api_user, api_pass=self.api_password)

        self.log.debug("Saving API token to config file")
        config['api_token'] = api_token

        self.log.debug("Setting API token in client")
        api.set_token(api_token=api_token)


class CathSelectTemplateManager(ApiClientManagerBase):
    """
    Selected template structure from sequence (via CATH API)

    Args:
        api_client (CathSelectTemplateClient): override default client (optional)
        base_url (str): create the default client with this base URL (optional)
    """

    def __init__(self, *, api_client=None, base_url=None, **kwargs):
        self._submit_data_cls = SubmitSelectTemplate
        client_args = {}
        if base_url:
            client_args['base_url'] = base_url
        if not api_client:
            api_client = clients.CathSelectTemplateClient(**client_args)

        self.task_uuid = None
        self.results_json = None
        self.scan_hits = None
        super().__init__(api_client=api_client, **kwargs)

    def run(self):

        api = self.api_client
        config = self._config

        self.log.info("Authenticating...")
        self.authenticate()
        self.log.info("  ... got token: %s", self.api_token)

        if not self.submit_data:
            self.log.debug("Loading data from file '%s' ...", self.infile)
            with open(self.infile) as infile:
                self.submit_data = SubmitSelectTemplate.load(infile)

        self.log.info("Submitting data ... ")
        self.log.debug("data: %s", self.submit_data.__dict__)
        submit_r = api.submit(data=self.submit_data)
        self.log.debug("response: %s", submit_r)
        self.task_uuid = submit_r['uuid']

        self.log.info("Checking status of task <%s> ...", self.task_uuid)
        while True:
            status_r = api.status(self.task_uuid)
            status = status_r['status'].upper()
            message = status_r['message']
            self.log.info("   [%s] %s", status, message)
            if status == 'SUCCESS':
                break
            if status == 'ERROR':
                self.log.error("Sequence search failed: %s", message)
                sys.exit(1)
            else:
                time.sleep(self.sleep)

        self.log.info("Retrieving scan results ... ")
        result_r = api.results(self.task_uuid)

        self.log.debug("result: %s", str(result_r)[:100])
        funfam_resolved_scan = self.funfam_resolved_scan()

        self.log.info("Resolved Funfam Matches:")
        hit_lines = funfam_resolved_scan.as_tsv().strip().split('\n')
        for hit_count, line in enumerate(hit_lines, 0):
            self.log.info("%-3s %s", hit_count if hit_count > 0 else '', line)

        if not funfam_resolved_scan.results:
            raise NoResultsError(
                "failed to get any results from funfam_resolved_scan")

    def hits(self):
        assert self.task_uuid

    def funfam_scan(self):
        """Returns the funfam scan results as :class:`cathpy.models.Scan`"""
        return self.api_client.funfam_scan()

    def funfam_resolved_scan(self):
        """Returns the resolved funfam scan results as :class:`cathpy.models.Scan`"""
        return self.api_client.funfam_resolved_scan()

    def funfam_resolved_scan_hits(self):
        """Returns the resolved funfam scan hits as [:class:`cathpy.models.ScanHit`]"""
        return self.api_client.funfam_resolved_scan().results[0].hits


class SMAlignmentManager(ApiClientManagerBase):
    """
    Generates 3D model from alignment data (via SWISS-MODEL API)
    """

    def __init__(self, *, api_client=None, **kwargs):
        if not api_client:
            api_client = clients.SMAlignmentClient()
        super().__init__(api_client=api_client, **kwargs)

    def run(self):

        api = self.api_client
        config = self._config

        self.authenticate()

        self.log.info("Submitting data ... ")
        if not self.submit_data:
            self.log.debug("Loading data from file '%s' ...", self.infile)
            with open(self.infile) as infile:
                self.submit_data = SubmitSelectTemplate.load(infile)

        submit_r = api.submit(data=self.submit_data)
        project_id = submit_r['project_id']

        self.log.info("Checking status of project <%s> ...", project_id)
        while True:
            status_r = api.status(project_id)
            status = status_r['status']
            self.log.info("   status: %s", status)
            if status == 'COMPLETED':
                break
            if status == 'FAILED':
                self.log.error("Modelling failed: %s", status_r['message'])
                sys.exit(1)
            else:
                time.sleep(self.sleep)

        self.log.info("Retrieving results ... ")
        result_r = api.results(project_id)

        def truncate_string(in_str):
            if isinstance(in_str, str) and len(in_str) > 100:
                in_str = str(in_str[:100] + '...')
            return in_str

        truncated_result = {k: truncate_string(
            v) for k, v in result_r.items()}
        self.log.debug("result: %s", truncated_result)
        coords = result_r['coordinates']

        self.log.info("Writing coordinates to %s", self.outfile)
        with open(self.outfile, 'w') as outfile:
            outfile.write(coords)
