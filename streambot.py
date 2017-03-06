# -*- coding: UTF-8 -*-

'''
streambot.py
'''
import boss
import downloader
import urlparse
import logging
import os

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
