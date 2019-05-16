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
from cathsm.apiclient.errors import ArgError, NoResultsError
from cathsm.apiclient import clients

DEFAULT_INFO_FORMAT = '%(asctime)s %(levelname)7s | %(message)s'
DEFAULT_DEBUG_FORMAT = '%(asctime)s %(name)-30s %(levelname)7s | %(message)s'
LOG = logging.getLogger(__name__)


class ApiClientManagerBase(object):

    def __init__(self, *, infile, outfile, api_client,
                 sleep=5, log_level=logging.INFO,
                 api_user=None, api_password=None, api_token=None,
                 config=None, config_section=None, clear_config=False):

        if not config_section:
            config_section = self.__class__.__name__

        if config is None:
            config = ApiConfig(section=config_section)
        else:
            config.section = config_section

        if clear_config:
            LOG.info("Clearing existing config for section: '%s'", config.section)
            config.delete_section()

        self.infile = infile
        self.outfile = outfile
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
            else:
                raise ArgError(
                    "expected 'api_token' or ('api_user', 'api_password')")

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

        passthrough_args = ('infile', 'outfile', 'sleep', 'clear_config',
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
            LOG.info("Setting API token ... ")
            api_token = self.api_token
        else:
            LOG.info("Authenticating via user/pass... (token_id not provided) ")
            LOG.debug("user: %s", self.api_user)
            api_token = api.authenticate(
                api_user=self.api_user, api_pass=self.api_password)

        LOG.debug("Saving API token to config file")
        config['api_token'] = api_token

        LOG.debug("Setting API token in client")
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

        self.results_json = None
        super().__init__(api_client=api_client, **kwargs)

    def run(self):

        api = self.api_client
        config = self._config

        LOG.info("IN_FILE:  %s", self.infile)
        LOG.info("OUT_FILE: %s", self.outfile)

        LOG.info("Authenticating...")
        self.authenticate()
        LOG.info("  ... got token: %s", self.api_token)

        LOG.info("Loading data from file '%s' ...", self.infile)
        with open(self.infile) as infile:
            submit_data = SubmitSelectTemplate.load(infile)

        LOG.info("Submitting data ... %s", str(submit_data.__dict__))
        submit_r = api.submit(data=submit_data)
        LOG.debug("response: %s", submit_r)
        task_id = submit_r['uuid']

        LOG.info("Checking status of task <%s> ...", task_id)
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

        LOG.debug("result: %s", str(result_r)[:100])

        funfam_resolved_scan = self.funfam_resolved_scan()

        LOG.info("Resolved Funfam Matches:")
        for line in funfam_resolved_scan.as_tsv().split('\n'):
            LOG.info("  %s", line)

        if not funfam_resolved_scan.results:
            raise NoResultsError(
                "failed to get any results from funfam_resolved_scan")

        scan_result = funfam_resolved_scan.results[0]
        for hit in scan_result.hits:
            LOG.info("hit: %s", hit)
            # get subsequence for "domain"
            #query_subseq = query_sequence.apply_segments([[hit.start, hit.stop]])

            # call endpoint that retrieves the alignment to best template in funfam hit

            # download funfam alignment
            #ff_align = download_funfam_alignment(hit.match)

            # get best domain for funfam
            # select_rep = SelectBlastRep(align=ff_align, ref_seq=query_subseq)
            # best_template = select_rep.get_best_blast_hit()

            # get pairwise alignment
            # mafft = MafftAddSequence(
            #     align=ff_align, sequence=self.query_subseq)
            # new_align = mafft.run()
            # merged_subseq = new_align.find_seq_by_id(self.query_subseq.id)

    def funfam_scan(self):
        """Returns the funfam scan results as :class:`cathpy.models.Scan`"""
        return self.api_client.funfam_scan()

    def funfam_resolved_scan(self):
        """Returns the resolved funfam scan results as :class:`cathpy.models.Scan`"""
        return self.api_client.funfam_resolved_scan()


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

        LOG.info("IN_FILE:  %s", self.infile)
        LOG.info("OUT_FILE: %s", self.outfile)

        self.authenticate()

        LOG.info("Loading data from file '%s' ...", self.infile)
        with open(self.infile) as infile:
            submit_data = SubmitAlignment.load(infile)

        LOG.info("Submitting data ... ")
        submit_r = api.submit(data=submit_data)
        project_id = submit_r['project_id']

        LOG.info("Checking status of project <%s> ...", project_id)
        while True:
            status_r = api.status(project_id)
            status = status_r['status']
            LOG.info("   status: %s", status)
            if status == 'COMPLETED':
                break
            if status == 'FAILED':
                LOG.error("Modelling failed: %s", status_r['message'])
                sys.exit(1)
            else:
                time.sleep(self.sleep)

        LOG.info("Retrieving results ... ")
        result_r = api.results(project_id)

        def truncate_string(in_str):
            if isinstance(in_str, str) and len(in_str) > 100:
                in_str = str(in_str[:100] + '...')
            return in_str

        truncated_result = {k: truncate_string(
            v) for k, v in result_r.items()}
        LOG.debug("result: %s", truncated_result)
        coords = result_r['coordinates']

        LOG.info("Writing coordinates to %s", self.outfile)
        with open(self.outfile, 'w') as outfile:
            outfile.write(coords)
