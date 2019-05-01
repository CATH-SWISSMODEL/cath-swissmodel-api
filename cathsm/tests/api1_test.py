# core
import json
import os
import configparser
import tempfile
import unittest

# local
from cathsm.apiclient.config import ApiConfig
from cathsm.apiclient.clients import CathSelectTemplateApiClient
from cathsm.apiclient.managers import CathSelectTemplateApiClientManager

DELETE_TEMP_FILES=False

EXAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'example_data')
EXAMPLE_USER='junk@sillit.com'
EXAMPLE_PASSWORD='FJRbnz'

class CathSelectTemplateApiClientTest(unittest.TestCase):

    def test_defaults(self):
        client = CathSelectTemplateApiClient()
        self.assertIsInstance(client, CathSelectTemplateApiClient)
            
        base_url = client.base_url
        self.assertEqual(base_url, 'http://www.cathdb.info/cathsm-api')

        self.assertEqual(
            client.get_url('submit'),
            base_url + '/select-template/')
        
        self.assertEqual(
            client.get_url('status', {"task_id": "foo"}),
            base_url + '/select-template/foo/')
        
        self.assertEqual(
            client.get_url('results', {"task_id": "foo"}),
            base_url + '/select-template/foo/results')


class SMAlignmentClientTest(unittest.TestCase):

    def test_defaults(self):

        infile = os.path.join(EXAMPLE_DATA_PATH, 'select-template-01.json')

        # run with user auth
        outfile1 = tempfile.NamedTemporaryFile(delete=DELETE_TEMP_FILES)
        client1 = CathSelectTemplateClient(infile=infile, outfile=outfile1.name, 
            api_user=EXAMPLE_USER, api_password=EXAMPLE_PASSWORD)
        client1.run()

        api_token = client1.api_token

        # run with token auth
        outfile2 = tempfile.NamedTemporaryFile(delete=DELETE_TEMP_FILES)
        client2 = CathSelectTemplateClient(infile=infile, outfile=outfile2.name, 
            api_token=api_token)
        client2.run()
        self.assertTrue(os.path.isfile(outfile2.name), 'outfile exists (token auth)')

