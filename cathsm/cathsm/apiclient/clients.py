"""
Clients that provide interaction with CATH / SWISS-MODEL API.
"""

# core
import logging

# non-core
import requests

# local
from cathsm.apiclient.errors import AuthenticationError

DEFAULT_SM_BASE_URL = 'https://beta.swissmodel.expasy.org'

# currently you have to start this yourself...
# cd ../cathapi && python3 manage.py runserver
DEFAULT_CATH_BASE_URL = 'http://localhost:8000'


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

    def check_response(self, *, response, status_success=200):
        if response.status_code != status_success:
            LOG.error("Error: failed to submit data: status=%s (expected %s), msg=%s",
                response.status_code, response.text, status_success)
            response.raise_for_status()
        try:
            response_data = response.json()
        except:
            LOG.error("failed to get json from response: %s", response)
            raise
        return response_data

    def submit(self, *, data=None, replacement_fields=None, status_success=201):
        """Submits the alignment data for modelling."""

        r = self.send_request(
            method='POST', 
            action='submit', 
            data=data, 
            replacement_fields=replacement_fields)

        r = self.process_submit_response(r)

        response_data = self.check_response(response=r, status_success=status_success)

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

        r = self.process_status_response(r)

        response_data = self.check_response(response=r, status_success=status_success)

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

        r = self.process_results_response(r)

        response_data = self.check_response(response=r, status_success=status_success)

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
        return res

    def process_authenticate_response(self, res):
        """Hook to allow manipulation/inspection of response to `authenticate` action"""
        return res

    def process_submit_response(self, res):
        """Hook to allow manipulation/inspection of response to `submit` action"""
        return res

    def process_status_response(self, res):
        """Hook to allow manipulation/inspection of response to `status` action"""
        return res

    def process_results_response(self, res):
        """Hook to allow manipulation/inspection of response to `results` action"""
        return res

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


class CathSelectTemplateApiClient(SubmitStatusResultsApiClient):
    """
    Client for API 1 (CATH)

    http://www.cathdb.info/search/by_funfhmmer

    TODO: generate the API paths dynamically via OpenAPI spec(?)
    """

    default_auth_url = '/api/api-token-auth/'
    default_submit_url = '/api/select-template/'
    default_status_url = '/api/select-template/{task_id}/'
    default_results_url = '/api/select-template/{task_id}/results'

    def __init__(self, *,
                 base_url=DEFAULT_CATH_BASE_URL,
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

    def status(self, task_id):
        """Retrieves the status of an existing task"""
        return super().status(replacement_fields={"task_id": task_id})

    def results(self, task_id):
        """Retrieves the results of an existing task"""
        return super().results(replacement_fields={"task_id": task_id})
