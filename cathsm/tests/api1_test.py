# core
import os
import tempfile
import unittest

# local
from cathsm.apiclient import clients, managers

DELETE_TEMP_FILES=False

EXAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'example_data')
EXAMPLE_USER='apitest'
EXAMPLE_PASSWORD='Aaewfijbovf12c12ecwerbq'

class CathSelectTemplateClientTest(unittest.TestCase):

    def test_defaults(self):
        client = clients.CathSelectTemplateClient()
        self.assertIsInstance(client, clients.CathSelectTemplateClient)
            
        base_url = client.base_url
        # self.assertEqual(base_url, 'http://www.cathdb.info/cathsm-api')
        self.assertEqual(base_url, 'http://localhost:8000')

        self.assertEqual(
            client.get_url('submit'),
            base_url + '/api/select-template/')
        
        self.assertEqual(
            client.get_url('status', {"task_id": "foo"}),
            base_url + '/api/select-template/foo/')
        
        self.assertEqual(
            client.get_url('results', {"task_id": "foo"}),
            base_url + '/api/select-template/foo/results')


class CathSelectTemplateManagerTest(unittest.TestCase):

    def test_defaults(self):

        infile = os.path.join(EXAMPLE_DATA_PATH, 'select-template-01.json')

        # run with user auth
        outfile1 = tempfile.NamedTemporaryFile(delete=DELETE_TEMP_FILES)
        client1 = managers.CathSelectTemplateManager(infile=infile, outfile=outfile1.name,
            api_user=EXAMPLE_USER, api_password=EXAMPLE_PASSWORD)
        client1.run()

        api_token = client1.api_token

        # run with token auth
        outfile2 = tempfile.NamedTemporaryFile(delete=DELETE_TEMP_FILES)
        client2 = managers.CathSelectTemplateManager(infile=infile, outfile=outfile2.name, 
            api_token=api_token)
        client2.run()
        self.assertTrue(os.path.isfile(outfile2.name), 'outfile exists (token auth)')

