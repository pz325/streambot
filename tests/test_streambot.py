import unittest
import streambot
import os
import logging
import shutil

logging.basicConfig(level=logging.DEBUG)


class TastStreamBot(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_is_full_uri_http(self):
        uri = 'http://example.com'
        self.assertTrue(streambot.is_full_uri(uri))

    def test_is_full_uri_https(self):
        uri = 'https://example.com'
        self.assertTrue(streambot.is_full_uri(uri))

    def test_is_full_uri_false(self):
        uri = 'asdf'
        self.assertFalse(streambot.is_full_uri(uri))

    def test_create_download_task(self):
        uri = 'http://example.com/x.pdf'
        output_dir = 'output_dir'
        clear_local = True
        local = os.path.join(output_dir, 'x.pdf')
        task = streambot.create_download_task(uri, output_dir, clear_local)
        self.assertEqual(task.status, 'START')
        self.assertEqual(task.id, uri)
        self.assertEqual(task.command['uri'], uri)
        self.assertEqual(task.command['local'], local)
        self.assertEqual(task.command['clear_local'], clear_local)

    def test_create_download_task_error_when_uri_not_full(self):
        uri = 'asdf'
        output_dir = 'output_dir'
        clear_local = True
        with self.assertRaises(streambot.StreamBotError):
            streambot.create_download_task(uri, output_dir, clear_local)

    def test_download_and_save_to_error_when_uri_not_full(self):
        uri = 'asdf'
        output_dir = 'output_dir'
        clear_local = True
        with self.assertRaises(streambot.StreamBotError):
            streambot.download_and_save_to(uri, output_dir, clear_local)

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

    def test_download_and_save_to_error_when_download_fail(self):
        uri = 'http://not.exist/a.ts'
        output_dir = 'output_dir'
        clear_local = True
        with self.assertRaises(streambot.StreamBotError):
            streambot.download_and_save_to(uri, output_dir, clear_local)

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
