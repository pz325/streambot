import unittest
import os
import shutil

import streambot
import hls_streambot


class TastHLSPlaylist(unittest.TestCase):
    def setUp(self):
        self.master_playlist_uri = r'https://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8'
        self.media_playlist_uri = r'https://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/gear1/prog_index.m3u8'
        self.master_playlist = hls_streambot.HLSPlaylist(self.master_playlist_uri)
        self.media_playlist = hls_streambot.HLSPlaylist(self.media_playlist_uri)
        self.output_dir = 'output_dir'

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_constructor(self):
        self.assertEqual(self.master_playlist.uri, self.master_playlist_uri)
        self.assertEqual(self.master_playlist.playlist, None)

    def test_consturctor_error_when_uri_is_not_full(self):
        uri = 'asdf'
        with self.assertRaises(streambot.StreamBotError):
            hls_streambot.HLSPlaylist(uri)

    def test_master_playlist_is_variant_true(self):
        self.master_playlist.download_and_save(self.output_dir)
        self.assertTrue(self.master_playlist.is_variant())

    def test_master_playlist_parse_media_playlists(self):
        self.master_playlist.download_and_save(self.output_dir)
        media_playlists = self.master_playlist.parse_media_playlists()
        self.assertEqual(len(media_playlists), 15)

    def test_master_playlist_parse_segments(self):
        self.master_playlist.download_and_save(self.output_dir)
        segments = self.master_playlist.parse_segments()
        self.assertEqual(len(segments), 0)

    def test_media_playlist_is_variant_false(self):
        self.media_playlist.download_and_save(self.output_dir)
        self.assertFalse(self.media_playlist.is_variant())

    def test_media_playlist_parse_media_playlists(self):
        self.media_playlist.download_and_save(self.output_dir)
        media_playlists = self.media_playlist.parse_media_playlists()
        self.assertEqual(len(media_playlists), 0)

    def test_media_playlist_parse_segments(self):
        self.media_playlist.download_and_save(self.output_dir)
        segments = self.media_playlist.parse_segments()
        self.assertEqual(len(segments), 181)

    def test_media_playlist_is_live(self):
        self.media_playlist.download_and_save(self.output_dir)
        self.assertFalse(self.media_playlist.is_live())

    def test_media_playlist_target_duration(self):
        self.media_playlist.download_and_save(self.output_dir)
        self.assertEqual(self.media_playlist.target_duration(), 11)
