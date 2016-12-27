'''
downloader.py
'''

import logging
import os
import requests
logger = logging.getLogger('downloader.streambot')


def _download(uri, filename):
    '''
    download from uri and save as filename
    @param uri
    @param filename
    @return True if download succeeds
    '''
    try:
        resp = requests.get(uri, verify=False)
        resp.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(resp.content)
        return True
    except requests.exceptions.RequestException as e:
        logger.error('Error: RequestException while download {uri}'.format(uri=uri))
        logger.error(e)
        return False


def download(uri, local, clear_local=False):
    '''
    Download resource from uri, save to local, i.e. path/to/target.file (relative to CWD)

    @param uri Full URI of the target
    @param local path/to/target.file
    @clear_local True if force to clear local
    @return True indicate download succeeds
    '''
    logger.debug('downloading {uri} to {local}'.format(uri=uri, local=local))
    if os.path.exists(local):
        if clear_local:
            os.remove(local)
        else:
            logger.debug('{local} exists'.format(local=local))
            return True

    try:
        subfolder = os.path.dirname(local)
        if subfolder and not os.path.exists(subfolder):
            os.makedirs(subfolder)
    except OSError as e:
        logger.error('Error: OSError while create folder {subfolder}'.format(subfolder=subfolder))
        logger.error(e)
        return False

    return _download(uri, local)


def _example():
    logging.basicConfig(level=logging.DEBUG)
    uri = r'https://bootstrap.pypa.io/get-pip.py'
    local = r'C:\Users\Ping\Downloads\apip.py'
    r = download(uri, local, clear_local=True)
    if r:
        logger.debug('download {uri} succeeds'.format(uri=uri))

    if os.path.exists(local):
        logger.debug('{local} exist'.format(local=local))

    uri = r'http://bad.url.example/not.exist'
    r = download(uri, local, clear_local=True)
    if not r:
        logger.debug('download {uri} fails'.format(uri=uri))

    if os.path.exists(local):
        os.remove(local)


if __name__ == '__main__':
    _example()
