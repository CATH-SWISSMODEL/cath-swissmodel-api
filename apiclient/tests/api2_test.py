import unittest

from apiclient.clients import SMAlignmentApiClient

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
