import unittest
import streambot
import os


class TastBot(unittest.TestCase):
    def setUp(self):
        self.bot = streambot.Bot()
        pass

    def tearDown(self):
        pass

    def test_num_worker(self):
        self.assertEqual(self.bot.num_worker, streambot._NUM_WORKER)

    def test_refresh_interval(self):
        self.assertEqual(self.bot.refresh_interval, streambot._REFRESH_INTERVAL)

    def test_total_length(self):
        self.assertEqual(self.bot.total_length, streambot._TOTAL_LENGTH)

    def test_output_dir(self):
        self.assertEqual(self.bot.output_dir, os.path.join(os.getcwd(), streambot._OUTPUT_DIR))
