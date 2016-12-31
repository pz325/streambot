import unittest
import streambot


class TastHLSSegment(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_consturctor_error_when_uri_is_not_full(self):
        uri = 'asdf'
        with self.assertRaises(streambot.StreamBotError):
            streambot.HLSSegment(uri)
