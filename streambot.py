'''
streambot.py
'''
import boss
import downloader
import urlparse
import logging
import os
import m3u8


logger = logging.getLogger('streambot.streambot')

_NUM_WORKER = 3
_REFRESH_INTERVAL = 5  # second
_TOTAL_LENGTH = 60  # second


def download_task_action(task):
    return downloader.download(task['uri'], task['local'], task['clear_local'])


class StreamBotError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Bot():
    def __init__(self):
        self.num_worker = _NUM_WORKER
        self.refresh_interval = _REFRESH_INTERVAL
        self.total_length = _TOTAL_LENGTH
        self.output_dir = os.getcwd()


class HLSStreamBot(Bot):
    '''
    Stream bot for HLS stream
    '''
    def __init__(self, master_stream_uri):
        Bot.__init__(self)
        self.master_stream_uri = master_stream_uri
        url = urlparse.urlparse(self.master_stream_uri)
        self.master_stream_local = os.path.join(self.output_dir, url.path[1:])
        logger.debug('master stream uri: {uri}'.format(uri=self.master_stream_uri))
        logger.debug('master stream local: {local}'.format(local=self.master_stream_local))

    def run(self):
        try:
            boss.start(num_workers=self.num_worker, action=download_task_action)
            self._download_master_playlist()
            self._parse_master_playlist()
            boss.stop()
        except Exception as e:
            logger.error(e)

    def _download_master_playlist(self):
        if not downloader.download(self.master_stream_uri, self.master_stream_local, clear_local=True):
            raise StreamBotError('Failed download master playlist from {uri}'.format(uri=self.master_stream_uri))

    def _parse_master_playlist(self):
        with open(self.master_stream_local, 'r') as f:
            content = f.read()
            self.master_playlist = m3u8.loads(content)


def _hls_stream_bot_example():
    logging.basicConfig(level=logging.DEBUG)
    master_stream_uri = r'http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8'
    hls_stream_bot = HLSStreamBot(master_stream_uri)
    hls_stream_bot.run()
    pass


if __name__ == '__main__':
    _hls_stream_bot_example()
