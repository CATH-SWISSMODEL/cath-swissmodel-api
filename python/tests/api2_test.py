# core
import logging
import os
import tempfile

# non-core
import requests

# local convenience
from . import testutils

logger = logging.getLogger(__name__)

class TestApi2(testutils.TestCase):
    """
    Run tests on API 2 (SWISSMODEL)
    
    Note: get detailed logs by setting environment var CATHSM_DEBUG=1
    """

    def setUp(self):

        self.base_url = 'http://beta.swissmodel.expasy.org'
        
        try:
            sm_user = os.environ['SWISSMODEL_USER'] 
        except:
            raise Exception('must specify environment variable SWISSMODEL_USER')

        try:
            sm_pass = os.environ['SWISSMODEL_PASSWORD'] 
        except:
            raise Exception('must specify environment variable SWISSMODEL_PASSWORD')

        self.auth_data=(sm_user, sm_pass)

        self.request_data = {
            "target_sequence": "KSCCPTTAARNQYNICRLPGTPRPVCAALSGCKIISGTGCPPGYRH",
            "template_sequence": "TTCCPSIVARSNFNVCRLPGTPEALCATYTGCIIIPGATCPGDYAN",
            "pdb_id": "1crn",
            "resnum_start": 0,
            "label_asym_id": "A",
            "assembly_id": 1
        }

        self.expected_response_data = {
            "target_sequence": "KSCCPTTAARNQYNICRLPGTPRPVCAALSGCKIISGTGCPPGYRH",
            "template_sequence": "TTCCPSIVARSNFNVCRLPGTPEALCATYTGCIIIPGATCPGDYAN",
            "resnum_start": 0,
            "pdb_id": "1crn",
            "label_asym_id": "A",
            "assembly_id": 1,
            "project_id": "jHXF9L"
        }

    def test_submit(self):
        r = requests.post(self.base_url + '/alignment', data=self.request_data, auth=self.auth_data)
        print( "response [{}]: {}".format(r.status_code, r.json()))
