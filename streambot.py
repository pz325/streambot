'''
streambot.py
'''
import boss
import downloader
import urlparse
import logging
import os
import m3u8
import time


logger = logging.getLogger('streambot.streambot')

_NUM_WORKER = 3
_REFRESH_INTERVAL = 5  # second
_TOTAL_LENGTH = 60  # second
_OUTPUT_DIR = 'output'


def _download_task_action(task):
    return downloader.download(task.command['uri'], task.command['local'], task.command['clear_local'])


def create_download_task(uri, output_dir, clear_local=False):
    '''
    @param uri Absolute URI
    '''
    if not is_full_uri(uri):
        raise StreamBotError('{uri} is not full URI'.format(uri=uri))

    url = urlparse.urlparse(uri)
    local = os.path.join(output_dir, url.path[1:])
    cmd = {'uri': uri, 'local': local, 'clear_local': clear_local}
    return boss.Task(uri, cmd, 'START')


def download_and_save_to(uri, output_dir, clear_local):
    '''
    Download URI and save content to output
    e.g. URI: http://host.com/path/to/playlist.m3u8
    then local is output_dir/path/to/playlist.m3u8
    @param uri Absolute URI
    @param output_dir
    @param clear_local True indicating to clear local
    @return local
    '''
    if not is_full_uri(uri):
        raise StreamBotError('{uri} is not full URI'.format(uri=uri))

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


class HLSSegment():
    def __init__(self, uri):
        '''
        @param uri Absolute URI of segment
        '''
        if not is_full_uri(uri):
            raise StreamBotError('HLSSegment URI is not absolute: {uri}'.format(uri=uri))

        self.uri = uri

    def log(self):
        logger.debug('Segment URI: {uri}'.format(uri=self.uri))


class HLSPlaylist():
    def __init__(self, uri):
        '''
        @param uri Absolute URI of playlist
        '''
        if not is_full_uri(uri):
            raise StreamBotError('HLSPlaylist URI is not absolute: {uri}'.format(uri=uri))

        self.uri = uri
        self.playlist = None

    def download_and_save(self, output_dir=_OUTPUT_DIR):
        '''
        download and save playlist
        also parse media playlists
        '''
        self.local = download_and_save_to(self.uri, output_dir, True)
        logger.debug('stream playlist is saved as: {local}'.format(local=self.local))

        with open(self.local, 'r') as f:
            content = f.read()
            self.playlist = m3u8.loads(content)

    def is_variant(self):
        return self.playlist.is_variant

    def log(self):
        logger.debug('Stream URI: {uri}'.format(uri=self.uri))
        if self.playlist.is_variant:
            media_playlists = self.parse_media_playlists()
            for m in media_playlists:
                logger.debug('Media playlist URI: {uri}'.format(uri=m.uri))
        else:
            segments = self.parse_segments()
            logger.debug('{n} segments in the list'.format(n=len(segments)))

    def parse_media_playlists(self):
        if not self.playlist.is_variant:
            return []

        playlists = []
        for p in self.playlist.playlists:
            uri = p.uri if is_full_uri(p.uri) else urlparse.urljoin(self.uri, p.uri)
            playlists.append(HLSPlaylist(uri))

        for m in self.playlist.media:
            if not m.uri:
                continue
            uri = m.uri if is_full_uri(p.uri) else urlparse.urljoin(self.uri, m.uri)
            playlists.append(HLSPlaylist(uri))
        return playlists

    def parse_segments(self):
        if self.playlist.is_variant:
            return []

        segments = []
        for s in self.playlist.segments:
            if s.uri.startswith('#'):
                continue
            if is_full_uri(s.uri):
                segments.append(HLSSegment(s.uri))
            else:
                segments.append(HLSSegment(urlparse.urljoin(self.uri, s.uri)))
        return segments


class HLSStreamBot(Bot):
    '''
    Stream bot for HLS stream
    '''
    def __init__(self, master_playlist_uri):
        Bot.__init__(self)
        self.master_playlist = HLSPlaylist(master_playlist_uri)
        logger.debug('master playlist URI: {uri}'.format(uri=self.master_playlist.uri))
        self.media_playlists = []

    def run(self):
        try:
            boss.start(num_workers=self.num_worker, action=_download_task_action)

            self.get_master_playlist()
            self.get_media_playlists()
            self.get_segments()

            while not boss.have_all_tasks_done():
                logger.debug('.........Waiting for all _TASKS done')
                time.sleep(1)
        except Exception as e:
            logger.exception(e)
        finally:
            boss.stop()

    def get_master_playlist(self):
        '''
        Download and save master playlist
        '''
        self.master_playlist.download_and_save()
        self.master_playlist.log()

    def get_media_playlists(self):
        if self.master_playlist.is_variant:
            self.media_playlists = self.master_playlist.parse_media_playlists()
        else:
            self.media_playlists.append(self.master_playlist)
        logger.debug('{n} playlists added'.format(n=len(self.media_playlists)))
        for m in self.media_playlists:
            m.download_and_save()

    def get_segments(self):
        '''
        Get and save segments from stream playlists
        '''
        # TODO: Implement a Breadth-First-Search
        for media_playlist in self.media_playlists:
            self.get_segments_from_playlist(media_playlist)

    def get_segments_from_playlist(self, playlist):
        '''
        Get and save segments from a playlist
        Assign download tasks to boss
        @param playlist
        '''
        segments = playlist.parse_segments()
        logger.debug('Download {n} segments from playlist {uri}'.format(n=len(segments), uri=playlist.uri))
        for s in segments:
            task = create_download_task(s.uri, self.output_dir)
            boss.assign_task(task)
            break


def _hls_stream_bot_example():
    logging.basicConfig(level=logging.DEBUG)
    master_stream_uri = r'http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8'
    hls_stream_bot = HLSStreamBot(master_stream_uri)
    hls_stream_bot.run()
    pass


if __name__ == '__main__':
    _hls_stream_bot_example()
