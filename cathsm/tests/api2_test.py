# core
import os
import tempfile
import unittest

# local
from cathsm.apiclient import clients, managers

DELETE_TEMP_FILES=False

EXAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'example_data')
EXAMPLE_USER='junk@sillit.com'
EXAMPLE_PASSWORD='FJRbnz'

class SMAlignmentClientTest(unittest.TestCase):

    def test_defaults(self):
        client = clients.SMAlignmentClient()
        self.assertIsInstance(client, clients.SMAlignmentClient)
        
        base_url = client.base_url
        self.assertEqual(base_url, 'https://beta.swissmodel.expasy.org')
        
        self.assertEqual(
            client.get_url('submit'),
            base_url + '/alignment/')
        
        self.assertEqual(
            client.get_url('status', {"project_id": "foo"}),
            base_url + '/alignment/foo/status/')
        
        self.assertEqual(
            client.get_url('results', {"project_id": "foo"}),
            base_url + '/alignment/foo/')

class SMAlignmentManagerTest(unittest.TestCase):

    def test_defaults(self):

        infile = os.path.join(EXAMPLE_DATA_PATH, 'A0PJE2__35-316.json')

        def atom_lines(pdbfile):
            atom_lines = None
            with open(pdbfile) as f:
                atom_lines = [f for line in f if line.startswith('ATOM')]
            return atom_lines

        # run with user auth
        outfile1 = tempfile.NamedTemporaryFile(delete=DELETE_TEMP_FILES)
        client1 = managers.SMAlignmentManager(infile=infile, outfile=outfile1.name, 
            api_user=EXAMPLE_USER, api_password=EXAMPLE_PASSWORD)
        client1.run()

        api_token = client1.api_token

        self.assertTrue(os.path.isfile(outfile1.name), 'outfile exists (user auth)')
        self.assertEqual(len(atom_lines(outfile1.name)), 2187, 'correct number of atoms')

        # run with token auth
        outfile2 = tempfile.NamedTemporaryFile(delete=DELETE_TEMP_FILES)
        client2 = managers.SMAlignmentManager(infile=infile, outfile=outfile2.name, 
            api_token=api_token)
        client2.run()
        self.assertTrue(os.path.isfile(outfile2.name), 'outfile exists (token auth)')
        self.assertEqual(len(atom_lines(outfile2.name)), 2187, 'correct number of atoms')

