"""
Clients that provide interaction with CATH / SWISS-MODEL API.
"""

# core
import logging
import sys
import time

# non-core
import requests

# local
from cathsm.apiclient.models import SubmitAlignment
from cathsm.apiclient.cli import ApiArgumentParser, ApiConfig
from cathsm.apiclient.errors import AuthenticationError, ArgError

DEFAULT_SM_BASE_URL = 'https://beta.swissmodel.expasy.org'

DEFAULT_INFO_FORMAT = '%(asctime)s %(levelname)7s | %(message)s'
DEFAULT_DEBUG_FORMAT = '%(asctime)s %(name)-30s %(levelname)7s | %(message)s'

LOG = logging.getLogger(__name__)

class ApiClientBase():
    """Base class for API clients."""

    def __init__(self, *, base_url, headers=None):
        self.base_url = base_url
        if not headers:
            headers = {}
        self.headers = headers

class SubmitStatusResultsApiClient(ApiClientBase):
    """Class for asynchronous API clients that follow a submit/status/result model."""

    def __init__(self, *, base_url, auth_url, submit_url, status_url, results_url):
        """Creates new client."""

        super().__init__(base_url=base_url)

        self.url_stems = {
            "auth": auth_url,
            "submit": submit_url,
            "status": status_url,
            "results": results_url,
        }

    def get_url(self, stem, replacement_fields=None):
        """Returns the URL allowing placeholders to be replaced by data"""

        if not replacement_fields:
            replacement_fields = {}

        url = self.url_stems[stem]
        url_parsed = url.format(**replacement_fields)
        full_url = self.base_url + url_parsed

        return full_url

    def send_request(self, action, replacement_fields=None, data=None, method="GET", headers=None):

        if data and type(data) is not dict:
            data = data.as_dict()

        if not replacement_fields:
            replacement_fields = data if data else {}

        if not headers:
            headers = self.headers

        url = self.get_url(action, replacement_fields)

        LOG.debug('{} {:50s}'.format(method, url))

        if method == "GET":
            r = requests.get(url, headers=self.headers)
        elif method == "POST":
            r = requests.post(url, data=data, headers=self.headers)
        else:
            raise Exception("unexpected API method {}".format(method))

        self.process_response(r)

        return r

    def submit(self, *, data=None, replacement_fields=None, status_success=201):
        """Submits the alignment data for modelling."""

        r = self.send_request(
            method='POST', 
            action='submit', 
            data=data, 
            replacement_fields=replacement_fields)

        self.process_submit_response(r)

        if r.status_code != status_success:
            LOG.error("Error: failed to submit data: status={} (expected {}), msg={}".format(
                r.status_code, r.text, status_success))
            r.raise_for_status()
        try:
            response_data = r.json()
        except:
            LOG.error("failed to get json from response: %s", r)
            raise

        return response_data

    def status(self, *, data=None, replacement_fields=None, status_success=200):
        """Returns the current status of the modelling task."""

        request_data = data.to_dict() if data else {}

        if not replacement_fields:
            replacement_fields = request_data

        r = self.send_request(
            method='GET',
            action='status',
            replacement_fields=replacement_fields)

        self.process_status_response(r)

        response_data = r.json()

        return response_data

    def results(self, *, data=None, replacement_fields=None, status_success=200):
        """Returns the results from the modelling task."""

        request_data = data.to_dict() if data else {}

        if not replacement_fields:
            replacement_fields = request_data

        r = self.send_request(
            method='GET',
            action='results',
            replacement_fields=replacement_fields)

        self.process_results_response(r)

        response_data = r.json()

        return response_data

    def set_token(self, *, api_token=None):
        LOG.debug('Using authorization token {}'.format(api_token))
        headers = {'Authorization': 'token {}'.format(api_token)}
        self.headers = headers

    def authenticate(self, *, api_user=None, api_pass=None):
        data = {'username': api_user, 'password': api_pass}
        LOG.debug('get_auth_headers.data: {}'.format(data))

        r = self.send_request(
            method='POST',
            action='auth',
            data=data,
            headers={'accept': 'application/json'})

        LOG.debug("auth_response [%s]: %s", r.status_code, r.json())
        response_data = r.json()
        if 'token' in response_data:
            token_id = response_data['token']
            LOG.debug('Using token {}'.format(token_id))
        else:
            raise AuthenticationError("failed to get token from response: {}".format(r.text))

        headers = {'Authorization': 'token {}'.format(token_id)}
        self.headers = headers
        return token_id

    def process_response(self, res):
        """Hook to allow manipulation/inspection of all responses"""
        pass

    def process_authenticate_response(self, res):
        """Hook to allow manipulation/inspection of response to `authenticate` action"""
        pass

    def process_submit_response(self, res):
        """Hook to allow manipulation/inspection of response to `submit` action"""
        pass

    def process_status_response(self, res):
        """Hook to allow manipulation/inspection of response to `status` action"""
        pass

    def process_results_response(self, res):
        """Hook to allow manipulation/inspection of response to `results` action"""
        pass


class SMAlignmentApiClient(SubmitStatusResultsApiClient):
    """
    Client for API 2 (SWISSMODEL)

    https://beta.swissmodel.expasy.org/swagger/

    [TODO]: generate the API paths dynamically via OpenAPI spec(?)
    """

    default_auth_url = '/api-token-auth/'
    default_submit_url = '/alignment/'
    default_status_url = '/alignment/{project_id}/status/'
    default_results_url = '/alignment/{project_id}/'

    def __init__(self, *,
                 base_url=DEFAULT_SM_BASE_URL,
                 auth_url=default_auth_url,
                 submit_url=default_submit_url,
                 status_url=default_status_url,
                 results_url=default_results_url
                ):

        # there has to be a nicer way of doing this?
        args = {
            "base_url": base_url,
            "auth_url": auth_url,
            "submit_url": submit_url,
            "status_url": status_url,
            "results_url": results_url,
        }
        super().__init__(**args)

    def submit(self, *, data):
        """Submits data to the API."""
        return super().submit(data=data)

    def status(self, project_id):
        """Retrieves the status of an existing project"""
        return super().status(replacement_fields={"project_id": project_id})

    def results(self, project_id):
        """Retrieves the results of an existing project"""
        return super().results(replacement_fields={"project_id": project_id})

class SMAlignmentClient(object):
    """
    Generates 3D model from alignment data (via SWISS-MODEL API)
    """

    def __init__(self, *, infile, outfile, api_user=None, api_password=None,
                 api_token=None, sleep=5, log_level=logging.INFO, config=None,
                 config_section=None, clear_config=False):
        
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

        self._apiclient = SMAlignmentApiClient()
        self._config = config

    @classmethod
    def new_from_cli(cls):
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

    def run(self):
    
        api = self._apiclient
        config = self._config

        LOG.info("DATA:  {}".format(self.infile))
        LOG.info("MODEL: {}".format(self.outfile))

        if self.api_token is not None:
            LOG.info("Setting API token ... ")
            api.set_token(api_token=self.api_token)
        else:
            LOG.info("Authenticating via user/pass... (token_id not provided) ")
            api_token = api.authenticate(api_user=self.api_user, api_pass=self.api_password)
            LOG.debug("Saving API token to config file")
            config['api_token'] = api_token

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

