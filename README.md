# streambot
A tool to download media Stream source as the stream playlist indicates.

HLS Clone Tool
=====================
# Clone HLS VOD
python hls_clone.py -u {URL} -o {output_path}

# Clone HLS LIVE
python hls_clone.py -u {URL} -o {output_path} -l {total_length_in_seconds}

Test
====
python -m unittest discover -s tests
python -m unittest tests.test_hlsstreambot