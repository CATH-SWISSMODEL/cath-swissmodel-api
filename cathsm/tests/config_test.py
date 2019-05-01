# core
import json
import os
import configparser
import tempfile
import unittest

# local
from cathsm.apiclient.config import ApiConfig
from cathsm.apiclient.clients import SMAlignmentApiClient
from cathsm.apiclient.managers import SMAlignmentApiClientManager

DELETE_TEMP_FILES=False

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

