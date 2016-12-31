# -*- coding: UTF-8 -*-

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
import sys

logger = logging.getLogger('streambot.streambot')

_NUM_WORKER = 3
_REFRESH_INTERVAL = None  # second
_TOTAL_LENGTH = 60  # second
_OUTPUT_DIR = 'output'


def _download_task_action(task):
    return downloader.download(task.command['uri'], task.command['local'], task.command['clear_local'])


def _get_local(uri, output_dir):
    url = urlparse.urlparse(uri)
    local = os.path.join(output_dir, url.path[1:])
    return local


def create_download_task(uri, output_dir, clear_local=False):
    '''
    @param uri Absolute URI
    '''
    if not is_full_uri(uri):
        raise StreamBotError('{uri} is not full URI'.format(uri=uri))

    local = _get_local(uri, output_dir)
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

    local = _get_local(uri, output_dir)
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
    def __init__(self, uri, is_byterange):
        '''
        @param uri Absolute URI of segment
        '''
        if not is_full_uri(uri):
            raise StreamBotError('HLSSegment URI is not absolute: {uri}'.format(uri=uri))

        self.uri = uri
        self.is_byterange = is_byterange

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
                segments.append(HLSSegment(uri=s.uri, is_byterange=s.byterange))
            else:
                segments.append(HLSSegment(uri=urlparse.urljoin(self.uri, s.uri), is_byterange=s.byterange))
        return segments

    def is_live(self):
        return not self.playlist.is_endlist

    def target_duration(self):
        return self.playlist.target_duration


class HLSStreamBot(Bot):
    '''
    Stream bot for HLS stream
    '''
    def __init__(self, master_playlist_uri):
        '''
        @param master_playlist_uri Absolute URI of the master playlist
        '''
        Bot.__init__(self)
        self.master_playlist = HLSPlaylist(master_playlist_uri)
        logger.debug('master playlist URI: {uri}'.format(uri=self.master_playlist.uri))
        self.media_playlists = []

    def run(self):
        try:
            boss.start(num_workers=self.num_worker, action=_download_task_action)

            self._get_master_playlist()
            self._get_media_playlists()
            if self.media_playlists[0].is_live():
                self._get_live_stream()
            else:
                self._get_segments()

            while not boss.have_all_tasks_done():
                time.sleep(1)

        except Exception as e:
            logger.exception(e)
        finally:
            boss.stop()
            self._report()

    def _get_live_stream(self):
        if not self.refresh_interval:
            self.refresh_interval = self.media_playlists[0].target_duration() / 2
        logger.debug('Refresh LIVE playlist at interval {interval} seconds'.format(interval=self.refresh_interval))
        length = 0
        while True:
            self._get_segments()
            time.sleep(self.refresh_interval)
            length += self.refresh_interval
            logger.debug('Refresh LIVE playlist for {length} seconds'.format(length=length))
            if length > self.total_length:
                break
            self._get_master_playlist()
            self._get_media_playlists()

    def _get_master_playlist(self):
        '''
        Download and save master playlist
        '''
        self.master_playlist.download_and_save()
        self.master_playlist.log()

    def _get_media_playlists(self):
        if self.master_playlist.is_variant:
            self.media_playlists = self.master_playlist.parse_media_playlists()
        else:
            self.media_playlists.append(self.master_playlist)
        logger.debug('{n} playlists added'.format(n=len(self.media_playlists)))
        for m in self.media_playlists:
            m.download_and_save()

    def _get_segments(self):
        '''
        Get and save segments from stream playlists
        '''
        # TODO: Implement a Breadth-First-Search
        for media_playlist in self.media_playlists:
            self._get_segments_from_playlist(media_playlist)

    def _get_segments_from_playlist(self, playlist):
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
            if s.is_byterange:
                break

    def _report(self):
        # check master playlist
        master_playlist_downloaded = os.path.exists(_get_local(self.master_playlist.uri, self.output_dir))
        mark = 'DONE' if master_playlist_downloaded else 'FAILED'
        sys.stdout.write('[{mark}] Master playlist {uri} \n'.format(mark=mark, uri=self.master_playlist.uri))
        # check media playlists
        for p in self.media_playlists:
            media_playlist_downloaded = os.path.exists(_get_local(p.uri, self.output_dir))
            mark = 'DONE' if media_playlist_downloaded else 'FAILED'
            sys.stdout.write('[{mark}] Media playlist {uri} \n'.format(mark=mark, uri=p.uri))
            segments = p.parse_segments()
            num_segments_downloaded = 0
            for s in segments:
                if os.path.exists(_get_local(s.uri, self.output_dir)):
                    num_segments_downloaded += 1
            sys.stdout.write('    [{num_downloaded}/{num_total}] Segments downloaded \n'.format(num_downloaded=num_segments_downloaded, num_total=len(segments)))
        sys.stdout.flush()
