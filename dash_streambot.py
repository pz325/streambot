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
import mpegdash

import streambot

logger = logging.getLogger('streambot.dash_streambot')


def _make_segment_url(mpd_base_url, period_base_url, adaptation_set_base_url, representation_base_url):
    mpd_base_url_value = mpd_base_url.base_url_value if mpd_base_url else ''
    period_base_url_value = period_base_url.base_url_value if period_base_url else ''
    adaptation_set_base_url_value = adaptation_set_base_url.base_url_value if adaptation_set_base_url else ''
    representation_base_url_value = representation_base_url.base_url_value if representation_base_url else ''

    if streambot.is_full_uri(representation_base_url_value):
        return representation_base_url_value

    url = ''.join([mpd_base_url_value, period_base_url_value, adaptation_set_base_url_value, representation_base_url_value])
    return url


def _check_is_byterange(mpd_base_url, period_base_url, adaptation_set_base_url, representation_base_url):
    mpd_is_byterange = mpd_base_url.byte_range if mpd_base_url else False
    period_is_byterange = period_base_url.byte_range if period_base_url else False
    adaptation_set_is_byterange = adaptation_set_base_url.byte_range if adaptation_set_base_url else False
    representation_is_byterange = representation_base_url.byte_range if representation_base_url else False
    return mpd_is_byterange or period_is_byterange or adaptation_set_is_byterange or representation_is_byterange


class DASHSegment():
    def __init__(self, uri, is_byterange=False):
        '''
        @param uri Absolute URI of segment
        @param is_byterange Default False
        '''
        if not streambot.is_full_uri(uri):
            raise streambot.StreamBotError('DASHSegment URI is not absolute: {uri}'.format(uri=uri))

        self.uri = uri
        self.is_byterange = is_byterange

    def log(self):
        logger.debug('Segment URI: {uri}'.format(uri=self.uri))


class MPD():
    def __init__(self, mpd_uri):
        '''
        @param mpd_uri Absolute URI of playlist
        '''
        if not streambot.is_full_uri(mpd_uri):
            raise streambot.StreamBotError('DASHPlaylist URI is not absolute: {uri}'.format(uri=mpd_uri))

        self.uri = mpd_uri
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

    def parse_segments(self):
        '''
        Parse segment URLs from MPD

        Support Single Segment URL, Segment timeline, and Segment template
        @return List of segment URLs
        '''
        mpd_base_url = self.mpd.base_urls[0] if self.mpd.base_urls else None
        segments = []
        for period in self.mpd.periods:
            period_base_url = period.base_urls[0] if period.base_urls else None
            if period.segment_lists:
                segments = self._get_segments_from_period_segment_list(period)
            elif period.segment_templates:
                segments = self._get_segments_from_period_segment_template(period)
            else:
                for adaptation_set in period.adaptation_sets:
                    adaptation_set_base_url = adaptation_set.base_urls[0] if adaptation_set.base_urls else None
                    if adaptation_set.segment_lists:
                        segments = self._get_segments_from_adaptation_set_segment_list(period, adaptation_set)
                    elif adaptation_set.segment_templates:
                        segments = self._get_segments_from_adaptation_set_segment_template(period, adaptation_set)
                    else:
                        for representation in adaptation_set.representations:
                            representation_base_url = representation.base_urls[0] if representation.base_urls else None
                            if representation.segment_lists:
                                segments = self._get_segments_from_representation_segment_list(period, adaptation_set, representation)
                            elif representation.segment_templates:
                                segments = self._get_segments_from_representation_segment_template(period, adaptation_set, representation)
                            else:
                                # case of single segment URL
                                segment_url = _make_segment_url(mpd_base_url, period_base_url, adaptation_set_base_url, representation_base_url)
                                is_byterange = _check_is_byterange(mpd_base_url, period_base_url, adaptation_set_base_url, representation_base_url)
                                segments.append(DASHSegment(segment_url, is_byterange))

        return segments


class DASHStreamBot(streambot.Bot):
    '''
    Stream bot for DASH stream
    '''
    def __init__(self, mpd_uri):
        '''
        @param mpd_uri Absolute URI of the master playlist
        '''
        streambot.Bot.__init__(self)
        self.uri = mpd_uri
        self.mpd = MPD(self.uri)
        logger.debug('MPD URI: {uri}'.format(uri=self.mpd.uri))

    def run(self):
        try:
            boss.start(num_workers=self.num_worker, action=streambot._download_task_action)
            self._get_mpd()
            if self.mpd.is_live():
                self._get_live_segments()
            else:
                self._get_segments()

            while not boss.have_all_tasks_done():
                time.sleep(1)

        except Exception as e:
            logger.exception(e)
        finally:
            boss.stop()
            self._report()

    def _get_mpd(self):
        self.mpd.download_and_save()

    def _get_live_segments(self):
        pass

    def _get_segments(self):
        segments = self.mpd.parse_segments()
        logger.debug('Download {n} segments from mpd {uri}'.format(n=len(segments), uri=self.mpd.uri))
        for s in segments:
            task = streambot.create_download_task(s.uri, self.output_dir)
            boss.assign_task(task)
            if s.is_byterange:
                break

        for s in segments:
            print(s.uri)

    def _report(self):
        pass


def _test():
    mpd_url = 'http://dash.akamaized.net/dash264/TestCases/1a/netflix/exMPD_BIP_TC1.mpd'
    bot = DASHStreamBot(mpd_url)
    bot._get_mpd()
    bot._get_segments()


if __name__ == '__main__':
    _test()
