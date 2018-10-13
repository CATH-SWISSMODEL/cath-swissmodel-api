# core
import logging
import os
import tempfile
import re

# non-core
import requests

# local convenience
from . import testutils

TEST_USER='junk@sillit.com'
TEST_PASSWORD='FJRbnz'

logger = logging.getLogger(__name__)

class TestApi2(testutils.TestCase):
    """
    Run tests on API 2 (SWISSMODEL)

    https://beta.swissmodel.expasy.org/swagger/

    Note: get detailed logs by setting environment var CATHSM_DEBUG=1
    """

    def setUp(self):

        self.base_url = 'https://beta.swissmodel.expasy.org'

        self.sm_user = os.environ['SWISSMODEL_USER'] if 'SWISSMODEL_USER' in os.environ else TEST_USER
        self.sm_pass = os.environ['SWISSMODEL_PASSWORD'] if 'SWISSMODEL_PASSWORD' in os.environ else TEST_PASSWORD

        self.incorrect_auth_header = {'Authorization': 'token 0123456789abcdef0123456789abcdef01234567'}

        self.request_data = {
            "target_sequence": "KSCCPTTAARNQYNICRLPGTPRPVCAALSGCKIISGTGCPPGYRH",
            "template_sequence": "TTCCPSIVARSNFNVCRLPGTPEALCATYTGCIIIPGATCPGDYAN",
            "pdb_id": "1crn",
            "resnum_start": 0,
            "label_asym_id": "A",
            "assembly_id": 1,
        }

        self.expected_response_data = {
            "target_sequence": "KSCCPTTAARNQYNICRLPGTPRPVCAALSGCKIISGTGCPPGYRH",
            "template_sequence": "TTCCPSIVARSNFNVCRLPGTPEALCATYTGCIIIPGATCPGDYAN",
            "resnum_start": 0,
            "pdb_id": "1crn",
            "label_asym_id": "A",
            "assembly_id": 1,
            "project_id": 'jHXF9L',
        }

    def test_submit(self):        
        submit_url = '{}/alignment/'.format(self.base_url)
        r = requests.post(submit_url, data=self.request_data)
        self.assertEqual(r.status_code, 401, 'submitting alignment without auth should return unauthorised (401)')

        r = requests.post(submit_url, data=self.request_data, headers=self.incorrect_auth_header)
        self.assertEqual(r.status_code, 401, 'submitting alignment with made up auth token should return unauthorised (401)')

        headers = self.get_auth_headers()
        r = requests.post(submit_url, data=self.request_data, headers=headers)
        self.assertEqual(r.status_code, 201, 'submitting alignment with correct auth token should return 201')
        response_data = r.json()

        self.assertDictEqual(response_data, self.expected_response_data)
        project_id = response_data['project_id']

        self.assertRegex(project_id, r'^[a-zA-Z0-9]{6}$')

        status_url = '{}/alignment/{}/status/'.format(self.base_url, project_id)
        r = requests.get(status_url)
        self.assertEqual(r.status_code, 401, 'unauthorised request should return 401')

        r = requests.get(status_url, headers=headers)
        self.assertEqual(r.status_code, 200, 'authorised request should return 200')
        print( "response [{}]: {}".format(r.status_code, r.json()))
        response_data = r.json()

    def test_auth_headers(self):
        headers = self.get_auth_headers()
        self.assertTrue('Authorization' in headers)
        token = headers['Authorization']
        logger.info("auth_token: {}".format(token))
        self.assertRegex(token, r'^token\s+[0-9a-f]{40}')
    
    def get_auth_headers(self):
        data = { 'username': self.sm_user, 'password': self.sm_pass }
        logger.debug('get_auth_headers.data: {}'.format(data))
        headers = { 'accept': 'application/json' }
        r = requests.post(self.base_url + '/api-token-auth/', data=data, headers=headers)
        logger.debug( "auth_response [{}]: {}".format(r.status_code, r.json()))
        response_data = r.json()
        headers = {'Authorization': 'token {}'.format(response_data['token'])}
        return headers
