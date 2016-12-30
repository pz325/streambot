import unittest
import streambot


class TastHLSStreamBot(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_is_full_uri(self):
        uri = 'http://example.com'
        self.assertTrue(streambot.is_full_uri(uri))

        uri = 'https://example.com'
        self.assertTrue(streambot.is_full_uri(uri))

        uri = 'asdf'
        self.assertFalse(streambot.is_full_uri(uri))
