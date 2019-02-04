# core
import json
import os
import configparser
import tempfile
import unittest

# local
from cathsm.apiclient.config import ApiConfig
from cathsm.apiclient.clients import SMAlignmentApiClient, SMAlignmentClient

DELETE_TEMP_FILES=False

EXAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'example_data')
EXAMPLE_USER='junk@sillit.com'
EXAMPLE_PASSWORD='FJRbnz'

class SMAlignmentApiClientTest(unittest.TestCase):

    def test_defaults(self):
        client = SMAlignmentApiClient()
        self.assertIsInstance(client, SMAlignmentApiClient)
        
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

class ApiConfigTest(unittest.TestCase):

    def test_defaults(self):

        section1 = 'api1'
        section2 = 'api2'

        tmp_file = tempfile.NamedTemporaryFile(delete=DELETE_TEMP_FILES)
        config_fname = tmp_file.name
        tmp_file.close()

        def parse_config():
            conf = configparser.ConfigParser()
            conf.read(config_fname)
            d = {}
            for s in conf.sections():
                d[s] = dict(conf[s])
            return d

        config1 = ApiConfig(section=section1, filename=config_fname)
        
        self.assertIsNot(os.path.isfile(config_fname), 
            'config file does not exist at start')

        config1['foo'] = 'bar'
        self.assertDictEqual(parse_config(), {"api1": {"foo": "bar"} }, 
            'saved config data contains prefix')
        self.assertEqual(config1['foo'], 'bar',
            'prefix works as expected when retrieving data')

        config2 = ApiConfig(section=section2, filename=config_fname)
        config2['foo'] = 'barf'

        self.assertDictEqual(dict(parse_config()), {"api1": {"foo": "bar"}, "api2": {"foo": "barf"}}, 
            'same key different project looks okay')

        self.assertEqual(config2['foo'], 'barf',
            'prefix works as expected when retrieving data')

        config2['foo'] = 'bingo'
        config2['food'] = 'apple'

        self.assertDictEqual(parse_config(), {"api1": {"foo": "bar"}, "api2": {"foo": "bingo", "food": "apple"}},
            'add/updated data looks okay')

        config2.delete_section(section_id=section2)
        self.assertDictEqual(parse_config(), {"api1": {"foo": "bar"}}, 
            'delete_section() works okay')


class SMAlignmentClientTest(unittest.TestCase):

    def test_defaults(self):

        infile = os.path.join(EXAMPLE_DATA_PATH, 'A0PJE2__35-316.json')

        def atom_lines(pdbfile):
            atom_lines = None
            with open(pdbfile) as f:
                atom_lines = [f for line in f if line.startswith('ATOM')]
            return atom_lines

        # run with user auth
        outfile1 = tempfile.NamedTemporaryFile(delete=DELETE_TEMP_FILES)
        client1 = SMAlignmentClient(infile=infile, outfile=outfile1.name, 
            api_user=EXAMPLE_USER, api_password=EXAMPLE_PASSWORD)
        client1.run()

        api_token = client1.api_token

        self.assertTrue(os.path.isfile(outfile1.name), 'outfile exists (user auth)')
        self.assertEqual(len(atom_lines(outfile1.name)), 2187, 'correct number of atoms')

        # run with token auth
        outfile2 = tempfile.NamedTemporaryFile(delete=DELETE_TEMP_FILES)
        client2 = SMAlignmentClient(infile=infile, outfile=outfile2.name, 
            api_token=api_token)
        client2.run()
        self.assertTrue(os.path.isfile(outfile2.name), 'outfile exists (token auth)')
        self.assertEqual(len(atom_lines(outfile2.name)), 2187, 'correct number of atoms')

