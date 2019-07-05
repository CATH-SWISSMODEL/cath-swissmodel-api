"""
Clients that provide interaction with CATH / SWISS-MODEL API.
"""

# core
import logging
import json
import re

# non-core
import requests
from pyswagger import App, Security
from pyswagger.contrib.client.requests import Client
from pyswagger.utils import jp_compose
from cathpy import funfhmmer
import cathpy.models

# local
from cathsm.apiclient.errors import InvalidTokenError, AuthenticationError, NoResultsError

DEFAULT_SM_BASE_URL = 'https://beta.swissmodel.expasy.org'

# currently you have to start this yourself...
# cd ../cathapi && python3 manage.py runserver
#DEFAULT_CATH_BASE_URL = 'http://localhost:8000'
DEFAULT_CATH_BASE_URL = 'https://api01.cathdb.info'


LOG = logging.getLogger(__name__)


class ApiClientBase():
    """Base class for API clients."""

    def __init__(self, *, base_url, auth_url, swagger_url=None, api_token=None, headers=None):
        self.base_url = base_url

        if not headers:
            headers = {}
        self.headers = headers

        self._api_token = None
        if api_token:
            self.set_token(api_token=api_token)

        self._url_stems = {}
        self.add_url_stem('auth', auth_url)
        self.add_url_stem('swagger', swagger_url)

    def add_url_stem(self, action, url_stem):
        if action in self._url_stems:
            raise Exception(
                'action {} already exists in url_stems'.format(action))
        self._url_stems[action] = url_stem

    def get_url(self, stem, replacement_fields=None):
        """Returns the URL allowing placeholders to be replaced by data"""

        if not replacement_fields:
            replacement_fields = {}

        url = self._url_stems[stem]
        url_parsed = url.format(**replacement_fields)
        full_url = self.base_url + url_parsed

        return full_url

    def send_request(self, *, action, method="GET", replacement_fields=None, data=None, headers=None):
        """
        Sends the request to the server and performs basic sanity checks on the response.

        Args:
            action (str): URL of the endpoint
            method (str): HTTP method to use (default: "GET")
            replacement_fields (dict): replace fields in the URL (optional)
            data (dict): send data (optional)

        Returns:
            response (:class:`requests.Response`): HTTP response object
        """
        if data and not isinstance(data, dict):
            data = data.as_dict()

        if not replacement_fields:
            replacement_fields = data if data else {}

        if not headers:
            headers = self.headers

        url = self.get_url(action, replacement_fields)

        LOG.info('{} {:50s}'.format(method, url))
        LOG.debug('headers: %s', str(self.headers))

        if method == "GET":
            res = requests.get(url, headers=self.headers)
        elif method == "POST":
            res = requests.post(url, data=data, headers=self.headers)
        else:
            raise Exception("unexpected API method {}".format(method))

        self.process_response(res)

        return res

    def check_response(self, *, response, status_success=200):

        if response.status_code == 401:
            if re.search(r'invalid token', response.text, re.IGNORECASE):
                raise InvalidTokenError('failed to authenticate client: submitted API token is invalid (try deleting and refreshing)')
            else:
                raise AuthenticationError('failed to authenticate client: {}'.format(response.text))

        if response.status_code != status_success:
            LOG.error("Error: failed to submit data: status=%s (expected %s), msg=%s",
                      response.status_code, status_success, response.text)
            response.raise_for_status()
        try:
            response_data = response.json()
        except:
            LOG.error("failed to get json from response: %s", response)
            raise
        return response_data

    def process_response(self, res):
        """Hook to allow manipulation/inspection of all responses"""
        return res

    def set_token(self, *, api_token=None):
        """Sets the token for the client."""
        self._api_token = api_token
        headers = {'Authorization': 'Token {}'.format(api_token)}
        self.headers = headers

    def authenticate(self, *, api_user=None, api_pass=None):
        """
        Authenticates the client.

        Args:
            api_user (str): username
            api_pass (str): password

        Returns:
            token_id (str): API token
        """

        data = {'username': api_user, 'password': api_pass}

        res = self.send_request(
            method='POST',
            action='auth',
            data=data,
            headers={'accept': 'application/json'})

        LOG.debug("auth_response [%s]: %s", res.status_code, res.json())
        response_data = res.json()
        if 'token' in response_data:
            token_id = response_data['token']
            LOG.debug('Using token %s', token_id)
        else:
            raise AuthenticationError(
                "failed to get token from response: {}".format(res.text))

        self.set_token(api_token=token_id)
        return token_id

    def process_authenticate_response(self, res):
        """Hook to allow manipulation/inspection of response to `authenticate` action"""
        return res

    def get_swagger(self):
        """Gets an authenticated Swagger Client."""

        swagger_url = self.get_url('swagger', replacement_fields={
                                   'base_url': self.base_url})

        # load Swagger resource file into App object
        app = App._create_(swagger_url)

        auth = Security(app)
        # TODO: this isn't working...
        # ValueError: Unknown security name: [api_key]
        auth.update_with('api_key', self._api_token)

        # init swagger client
        client = Client(auth)

        return app, client


class SubmitStatusResultsApiClient(ApiClientBase):
    """Class for asynchronous API clients that follow a submit/status/result model."""

    def __init__(self, *, base_url, auth_url, swagger_url, submit_url, status_url, results_url):
        """Creates new client."""

        super().__init__(base_url=base_url, auth_url=auth_url, swagger_url=swagger_url)

        self.add_url_stem('submit', submit_url)
        self.add_url_stem('status', status_url)
        self.add_url_stem('results', results_url)

    def submit(self, *, data=None, replacement_fields=None, status_success=201):
        """Submits the alignment data for modelling."""

        res = self.send_request(
            method='POST',
            action='submit',
            data=data,
            replacement_fields=replacement_fields)

        res = self.process_submit_response(res)

        response_data = self.check_response(
            response=res, status_success=status_success)

        return response_data

    def status(self, *, data=None, replacement_fields=None, status_success=200):
        """Returns the current status of the modelling task."""

        request_data = data.to_dict() if data else {}

        if not replacement_fields:
            replacement_fields = request_data

        res = self.send_request(
            method='GET',
            action='status',
            replacement_fields=replacement_fields)

        res = self.process_status_response(res)

        response_data = self.check_response(
            response=res, status_success=status_success)

        return response_data

    def results(self, *, data=None, replacement_fields=None, status_success=200):
        """Returns the results from the modelling task."""

        request_data = data.to_dict() if data else {}

        if not replacement_fields:
            replacement_fields = request_data

        res = self.send_request(
            method='GET',
            action='results',
            replacement_fields=replacement_fields)

        res = self.process_results_response(res)

        response_data = self.check_response(
            response=res, status_success=status_success)

        return response_data

    def process_submit_response(self, res):
        """Hook to allow manipulation/inspection of response to `submit` action"""
        return res

    def process_status_response(self, res):
        """Hook to allow manipulation/inspection of response to `status` action"""
        return res

    def process_results_response(self, res):
        """Hook to allow manipulation/inspection of response to `results` action"""
        return res


class SMAlignmentClient(SubmitStatusResultsApiClient):
    """
    Client for API 2 (SWISSMODEL)

    https://beta.swissmodel.expasy.org/swagger/

    [TODO]: generate the API paths dynamically via OpenAPI spec(?)
    """

    default_auth_url = '/api-token-auth/'
    default_swagger_url = '/swagger/?format=openapi'
    default_submit_url = '/alignment/'
    default_status_url = '/alignment/{project_id}/status/'
    default_results_url = '/alignment/{project_id}/'

    def __init__(self, *,
                 base_url=DEFAULT_SM_BASE_URL,
                 auth_url=default_auth_url,
                 swagger_url=default_swagger_url,
                 submit_url=default_submit_url,
                 status_url=default_status_url,
                 results_url=default_results_url
                 ):

        # there has to be a nicer way of doing this?
        args = {
            "base_url": base_url,
            "auth_url": auth_url,
            "swagger_url": swagger_url,
            "submit_url": submit_url,
            "status_url": status_url,
            "results_url": results_url,
        }
        super().__init__(**args)

    def submit(self, *, data):  # pylint: disable=W0221
        """Submits data to the API."""
        return super().submit(data=data)

    def status(self, project_id):  # pylint: disable=W0221
        """Retrieves the status of an existing project"""
        return super().status(replacement_fields={"project_id": project_id})

    def results(self, project_id):  # pylint: disable=W0221
        """Retrieves the results of an existing project"""
        return super().results(replacement_fields={"project_id": project_id})


class CathSelectTemplateClient(SubmitStatusResultsApiClient):
    """
    Client for API 1 (CATH)

    http://www.cathdb.info/search/by_funfhmmer

    TODO: generate the API paths dynamically via OpenAPI spec(?)
    """

    default_swagger_url = '/swagger/?format=openapi'
    default_auth_url = '/api/api-token-auth/'
    default_submit_url = '/api/select-template/'
    default_status_url = '/api/select-template/{task_id}/'
    default_results_url = '/api/select-template/{task_id}/results'

    def __init__(self, *,
                 base_url=DEFAULT_CATH_BASE_URL,
                 auth_url=default_auth_url,
                 swagger_url=default_swagger_url,
                 submit_url=default_submit_url,
                 status_url=default_status_url,
                 results_url=default_results_url
                 ):

        # there has to be a nicer way of doing this?
        args = {
            "base_url": base_url,
            "auth_url": auth_url,
            "swagger_url": swagger_url,
            "submit_url": submit_url,
            "status_url": status_url,
            "results_url": results_url,
        }
        self._result_response = None
        super().__init__(**args)

    def submit(self, *, data):    # pylint: disable=W0221
        """Submits data to the API."""
        return super().submit(data=data)

    def status(self, task_id):  # pylint: disable=W0221
        """Retrieves the status of an existing task"""
        return super().status(replacement_fields={"task_id": task_id})

    def results(self, task_id):  # pylint: disable=W0221
        """
        Retrieves the results of an existing task

        This method will also parse these results and make the `funfam_scan`
        and `funfam_resolved_scan` methods available. 

        Args:
            task_id (str): id of the task

        Returns:

        """
        cathsm_results_data = super().results(
            replacement_fields={"task_id": task_id})

        if not cathsm_results_data['results_json']:
            LOG.warning('failed to get any results (results_json is empty): %s', cathsm_results_data)
            # TODO: trying to indicate a result that corresponds to zero funfam
            # matches. Should be able to use valid query_fasta/cath_version 
            # and funfam_scan=None...
            results_data = {
                'query_fasta': None, 
                'funfam_scan': None, 
                'funfam_resolved_scan': None,
                'cath_version': None,
            }
        else:
            results_data = json.loads(cathsm_results_data['results_json'])
            LOG.debug("results_data: %s", str(results_data)[:100])

        self._result_response = funfhmmer.ResultResponse(**results_data)
        return cathsm_results_data

    def process_results_response(self, res):
        LOG.info("results.response: %s", res)
        return res

    @property
    def result_response(self):
        """
        Provides access to the response object (containing scan results)

        Returns:
            result_response (:class:`cathpy.funfhmmer.ResultResponse`)
        """
        if not self._result_response:
            raise NoResultsError(
                "cannot get funfam scan: results have not yet been retrieved")
        return self._result_response

    def funfam_scan(self):
        """
        Provides access to the scan results (all matches)

        Returns:
            scan (:class:`cathpy.models.Scan`): scan results for all FunFam matches

        Throws:
            NoResultsError: results must have been fetched before calling this method 
        """
        return self.result_response.funfam_scan

    def funfam_resolved_scan(self):
        """
        Provides access to the scan results (resolved to best domain matches)

        Returns:
            scan (:class:`cathpy.models.Scan`): scan results for resolved FunFam matches

        Throws:
            NoResultsError: results must have been fetched before calling this method 
        """
        return self.result_response.funfam_resolved_scan
