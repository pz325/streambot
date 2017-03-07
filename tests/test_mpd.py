import unittest
import os
import shutil
import streambot
import dash_streambot


class TastMPD(unittest.TestCase):
    def setUp(self):
        self.vod_url = r'http://dash.akamaized.net/dash264/TestCases/1a/netflix/exMPD_BIP_TC1.mpd'
        self.live_url = r'http://vm2.dashif.org/livesim-dev/periods_60/xlink_30/insertad_1/testpic_2s/Manifest.mpd'
        self.output_dir = 'output_dir'

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_constructor(self):
        playlist = dash_streambot.MPD(self.vod_url)
        self.assertEqual(playlist.uri, self.vod_url)

    def test_consturctor_error_when_uri_is_not_full(self):
        uri = 'asdf'
        with self.assertRaises(streambot.StreamBotError):
            dash_streambot.MPD(uri)

    def test_vod_is_live_false(self):
        vod_playlist = dash_streambot.MPD(self.vod_url)
        vod_playlist.download_and_save(self.output_dir)
        self.assertFalse(vod_playlist.is_live())

    def test_live_is_live_true(self):
        live_playlist = dash_streambot.MPD(self.live_url)
        live_playlist.download_and_save(self.output_dir)
        self.assertTrue(live_playlist.is_live())

    def test_parse_segments_single_segment_URL(self):
        url = r'http://dash.akamaized.net/dash264/TestCases/1a/netflix/exMPD_BIP_TC1.mpd'
        mpd = dash_streambot.MPD(url)
        mpd.download_and_save()
        segments = mpd.parse_segments()
        self.assertEqual(segments[0].uri, r'http://dash.edgesuite.net/dash264/TestCases/1a/netflix/ElephantsDream_AAC48K_064.mp4.dash')
        self.assertEqual(segments[1].uri, r'http://dash.edgesuite.net/dash264/TestCases/1a/netflix/ElephantsDream_H264BPL30_0100.264.dash')
        self.assertEqual(segments[2].uri, r'http://dash.edgesuite.net/dash264/TestCases/1a/netflix/ElephantsDream_H264BPL30_0175.264.dash')
        self.assertEqual(segments[3].uri, r'http://dash.edgesuite.net/dash264/TestCases/1a/netflix/ElephantsDream_H264BPL30_0250.264.dash')
        self.assertEqual(segments[4].uri, r'http://dash.edgesuite.net/dash264/TestCases/1a/netflix/ElephantsDream_H264BPL30_0500.264.dash')
        for s in segments:
            self.assertFalse(s.is_byterange)
