from mpegdash.parser import MPEGDASHParser

mpd_url = 'http://dash.akamaized.net/dash264/TestCases/1a/netflix/exMPD_BIP_TC1.mpd'
mpd = MPEGDASHParser.parse(mpd_url)
for p in mpd.periods:
    print('==== Period ====')
    print(p.__dict__)
    for s in p.adaptation_sets:
        print('==== adaptation set ====')
        print(s.__dict__)
        for r in s.representations:
            print('==== Representation ====')
            print(r.__dict__)
            for b in r.base_urls:
                print(b.__dict__)
