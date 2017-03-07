import unittest
import streambot
import dash_streambot


class TastDASHSegment(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_constructor(self):
        uri = 'http://example.com/1.ts'
        is_byterange = True
        segment = dash_streambot.DASHSegment(uri, is_byterange)
        self.assertEqual(segment.uri, uri)
        self.assertEqual(segment.is_byterange, is_byterange)

    def test_constructor_default_is_byterange_false(self):
        uri = 'http://example.com/1.ts'
        segment = dash_streambot.DASHSegment(uri)
        self.assertEqual(segment.is_byterange, False)

    def test_constructor_error_when_uri_is_not_full(self):
        uri = 'asdf'
        is_byterange = True
        with self.assertRaises(streambot.StreamBotError):
            dash_streambot.DASHSegment(uri, is_byterange)
