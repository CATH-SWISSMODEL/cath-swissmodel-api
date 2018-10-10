# core
import logging
import os
import tempfile
import re

# non-core
import requests

# local convenience
from . import testutils

logger = logging.getLogger(__name__)

class TestApi2(testutils.TestCase):
    """
    Run tests on API 2 (SWISSMODEL)

    https://beta.swissmodel.expasy.org/swagger/

    Note: get detailed logs by setting environment var CATHSM_DEBUG=1
    """

    def setUp(self):

        self.base_url = 'https://beta.swissmodel.expasy.org'

        try:
            self.sm_user = os.environ['SWISSMODEL_USER'] 
        except:
            raise Exception('must specify environment variable SWISSMODEL_USER')

        try:
            self.sm_pass = os.environ['SWISSMODEL_PASSWORD'] 
        except:
            raise Exception('must specify environment variable SWISSMODEL_PASSWORD')

        self.expected_project_id = 'jHXF9L'

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
            "project_id": self.expected_project_id,
        }

    def test_submit(self):        
        submit_url = '{}/alignment/'.format(self.base_url)
        r = requests.post(submit_url, data=self.request_data)
        self.assertEqual(r.status_code, 401, 'should get unauthorised code')

        headers = self.get_auth_headers()
        r = requests.post(submit_url, data=self.request_data, headers=headers)
        self.assertEqual(r.status_code, 201, 'return status should be 201')
        response_data = r.json()

        self.assertDictEqual(response_data, self.expected_response_data)
        project_id = response_data['project_id']
        self.assertEqual(project_id, self.expected_project_id)

    def test_auth_headers(self):
        headers = self.get_auth_headers()
        self.assertTrue('Authorization' in headers)
        token = headers['Authorization']
        logger.info("auth_token: {}".format(token))
        self.assertRegex(token, r'^token\s+[0-9a-f]{40}')
        
    def test_project_status(self):
        status_url = '{}/alignment/{}/status/'.format(self.base_url, self.expected_project_id)
        r = requests.get(status_url)
        self.assertEqual(r.status_code, 401, 'unauthorised request should return 401')
        headers = { }
        r = requests.get(status_url, headers)
        self.assertEqual(r.status_code, 401, 'unauthorised request should return 401')
        print( "response [{}]: {}".format(r.status_code, r.json()))
        response_data = r.json()

    def get_auth_headers(self):
        data = { 'username': self.sm_user, 'password': self.sm_pass }
        headers = { 'accept': 'application/json' }
        r = requests.post(self.base_url + '/api-token-auth/', data=data, headers=headers)
        logger.debug( "auth_response [{}]: {}".format(r.status_code, r.json()))
        response_data = r.json()
        headers = {'Authorization': 'token {}'.format(response_data['token'])}
        return headers
