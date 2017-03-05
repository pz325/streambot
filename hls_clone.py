# -*- coding: UTF-8 -*-

'''
hls_clone tool
'''
import streambot
import logging


def parse_argument():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--uri', '-u', required=True, help='Master playlist URI')
    parser.add_argument('--output_dir', '-o', help='output_dir. Default is output_dir')
    parser.add_argument('--total_length', '-l', type=int, help='Total length of streams, in seconds, for downloading LIVE streams')
    parser.add_argument('--verbose', '-v', help="increase output verbosity", action="store_true")
    args = parser.parse_args()
    return args


def main():
    args = parse_argument()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    hls_stream_bot = streambot.HLSStreamBot(args.uri)
    if args.output_dir:
        hls_stream_bot.output_dir = args.output_dir

    if args.total_length:
        hls_stream_bot.total_length = args.total_length

    hls_stream_bot.run()

if __name__ == '__main__':
    main()

# python hls_clone.py -u http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8 -v
