# streambot
A tool to download media Stream source as the stream playlist indicates.

# HLS Clone Tool
## Clone HLS VOD
~~~~
python hls_clone.py -u {URL} -o {output_path}
~~~~

## Clone HLS LIVE
~~~~
python hls_clone.py -u {URL} -o {output_path} -l {total_length_in_seconds}
~~~~

## Encrypte HLS stream
tbc

# DASH Clone Tool
## Clone DASH VOD
tbc
## Clone DASH Live
tbc
## Encrypte DASH stream
tbc

# Test
~~~~
python -m unittest discover -s tests
python -m unittest tests.test_hlsstreambot
~~~~