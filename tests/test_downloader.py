import unittest
import downloader
import os


class TaskDownloader(unittest.TestCase):
    def setUp(self):
        self.uri = r'https://bootstrap.pypa.io/get-pip.py'
        self.local = r'local.todelete'

    def tearDown(self):
        if os.path.exists(self.local):
            os.remove(self.local)

    def test_clear_local(self):
        f = open(self.local, 'wb')
        f.close()
        f_create_time = os.path.getmtime(self.local)

        downloader.download(self.uri, self.local, clear_local=True)
        f_update_time = os.path.getmtime(self.local)
        self.assertNotEqual(f_create_time, f_update_time)

    def test_download_returns_False_if_uri_invalid(self):
        uri = r'http://bad.url.example/not.exist'
        r = downloader.download(uri, self.local)
        self.assertFalse(r)

    def test_download(self):
        self.assertFalse(os.path.exists(self.local))

        r = downloader.download(self.uri, self.local)
        self.assertTrue(r)
        self.assertTrue(os.path.exists(self.local))
