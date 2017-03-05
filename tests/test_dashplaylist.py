import unittest
import streambot
import os
import shutil


class TastDASHPlaylist(unittest.TestCase):
    def setUp(self):
        self.vod_url = r'http://dash.akamaized.net/dash264/TestCases/1a/netflix/exMPD_BIP_TC1.mpd'
        self.live_url = r'http://vm2.dashif.org/livesim-dev/periods_60/xlink_30/insertad_1/testpic_2s/Manifest.mpd'
        self.output_dir = 'output_dir'

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_constructor(self):
        playlist = streambot.DASHPlaylist(self.vod_url)
        self.assertEqual(playlist.uri, self.vod_url)

    def test_consturctor_error_when_uri_is_not_full(self):
        uri = 'asdf'
        with self.assertRaises(streambot.StreamBotError):
            streambot.DASHPlaylist(uri)

    def test_vod_is_live_false(self):
        vod_playlist = streambot.DASHPlaylist(self.vod_url)
        vod_playlist.download_and_save(self.output_dir)
        self.assertFalse(vod_playlist.is_live())

    def test_live_is_live_true(self):
        live_playlist = streambot.DASHPlaylist(self.live_url)
        live_playlist.download_and_save(self.output_dir)
        self.assertTrue(live_playlist.is_live())
