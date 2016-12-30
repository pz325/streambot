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
_OUTPUT_DIR = 'output'


def download_task_action(task):
    return downloader.download(task['uri'], task['local'], task['clear_local'])


def download_and_save_to(uri, output_dir, clear_local):
    '''
    Download URI and save content to output
    e.g. URI: http://host.com/path/to/playlist.m3u8
    then local is output_dir/path/to/playlist.m3u8
    @param uri
    @param output_dir
    @param clear_local True indicating to clear local
    @return local
    '''
    url = urlparse.urlparse(uri)
    local = os.path.join(output_dir, url.path[1:])
    if not downloader.download(uri, local, clear_local):
        raise StreamBotError('Failed download {uri}'.format(uri=uri))
    return local


def is_full_uri(uri):
    return uri.startswith('http://') or uri.startswith('https://')


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
        self.output_dir = os.path.join(os.getcwd(), _OUTPUT_DIR)


class HLSStreamBot(Bot):
    '''
    Stream bot for HLS stream
    '''
    def __init__(self, master_playlist_uri):
        Bot.__init__(self)
        self.master_playlist_uri = master_playlist_uri
        logger.debug('master playlist URI: {uri}'.format(uri=self.master_playlist_uri))

    def run(self):
        try:
            boss.start(num_workers=self.num_worker, action=download_task_action)
            self.get_master_playlist()
            self.get_streams()
        except Exception as e:
            logger.error(e)
        finally:
            boss.stop()

    def get_master_playlist(self):
        logger.debug('Get master laylist: {uri}'.format(uri=self.master_playlist_uri))
        master_playlist_local = download_and_save_to(self.master_playlist_uri, self.output_dir, True)
        logger.debug('master playlist is saved as: {local}'.format(local=master_playlist_local))

        with open(master_playlist_local, 'r') as f:
            content = f.read()
            self.master_playlist = m3u8.loads(content)

        logger.debug('master playlist is variant: {v}'.format(v=self.master_playlist.is_variant))
        logger.debug('strem playlists:')
        for playlist in self.master_playlist.playlists:
            logger.debug(playlist.uri)
        logger.debug('media playlist:')
        for m in self.master_playlist.media:
            if m.uri:
                logger.debug(m.uri)

    def get_streams(self):
        logger.debug('get streams')
        if self.master_playlist.is_variant:
            # download resource from stream playlist
            for playlist in self.master_playlist.playlists:
                self.get_stream_segments(playlist.uri)

            # download resource from media
            for m in self.master_playlist.media:
                if not m.uri:
                    continue
                self.get_stream_segments(m.uri)
        else:
            self.get_stream_segments(self.master_playlist_uri)

    def get_stream_segments(self, uri):
        if not is_full_uri(uri):
            uri = urlparse.urljoin(self.master_playlist_uri, uri)
        logger.debug('get segments from stream: {uri}'.format(uri=uri))
        pass


def _hls_stream_bot_example():
    logging.basicConfig(level=logging.DEBUG)
    master_stream_uri = r'http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8'
    hls_stream_bot = HLSStreamBot(master_stream_uri)
    hls_stream_bot.run()
    pass


if __name__ == '__main__':
    _hls_stream_bot_example()
