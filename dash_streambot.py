# -*- coding: UTF-8 -*-

'''
dash_streambot.py
'''
import boss
import urlparse
import logging
import os
import time
import sys
from mpegdash.parser import MPEGDASHParser

import streambot

logger = logging.getLogger('streambot.dash_streambot')


class MPD():
    def __init__(self, uri):
        '''
        @param uri Absolute URI of playlist
        '''
        if not streambot.is_full_uri(uri):
            raise streambot.StreamBotError('DASHPlaylist URI is not absolute: {uri}'.format(uri=uri))

        self.uri = uri
        self.mpd = None

    def download_and_save(self, output_dir=streambot._OUTPUT_DIR):
        '''
        download and save playlist
        also parse media playlists
        '''
        self.local = streambot.download_and_save_to(self.uri, output_dir, True)
        logger.debug('stream playlist is saved as: {local}'.format(local=self.local))

        with open(self.local, 'r') as f:
            content = f.read()
            self.mpd = MPEGDASHParser.parse(content)

    def is_live(self):
        return 'static' != self.mpd.type
