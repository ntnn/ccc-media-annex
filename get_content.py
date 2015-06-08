#!/usr/bin/env python3
# Author: Nelo-T. Wallus <nelo@wallus.de>
import json
import requests
import logging
from sys import argv
from subprocess import call

API_SERVER = 'http://api.media.ccc.de/'
API_PATH = {
    'conferences': '/public/conferences',
    'conference': '/public/conferences/',
    'events': '/public/events',
    'event': '/public/events/',
    'recordings': '/public/recordings',
    'recording': '/public/recordings/'
    }

logging.basicConfig(level=logging.ERROR)
LOGGER = logging.getLogger(__name__)


def request(key_or_url, ident=0):
    """Sends a request to the media server and returns a json dict.

    :type key_or_url: str
    :type ident: int
    :rtype: dict
    """
    if key_or_url.startswith('http'):
        url = key_or_url
    else:
        url = API_SERVER + API_PATH[key_or_url] + (
            str(ident) if not ident == 0 else '')
    LOGGER.info('Sending request to {}'.format(url))
    response = requests.request('GET', url).text
    return json.loads(response)


def get_recording_urls(key_or_url='recordings', ident=0):
    """Generator, yields recording urls for given keyword and ident.
    If no event was given all recordings are yielded.

    :type key_or_url: str
    :type ident: int
    :rtype: str
    """
    if not key_or_url.startswith('http'):
        if key_or_url not in ('recordings', 'event'):
            LOGGER.error('Invalid keyword.')
            return

    recordings = request(key_or_url, ident)['recordings']
    LOGGER.info('Grabbed info, start yielding')
    for record in recordings:
        yield record['recording_url']


def get_conference_events(ident):
    """Generator, yields json dicts of the events of a conference.

    :type ident: int
    :rtype: dict
    """
    events = request('conference', ident)['events']
    for event in events:
        yield event


def get_conference_recording_urls(ident):
    """Generator, yields url strings of the recordings of a conference.

    :type ident: int
    :rtype: str
    """
    for event in get_conference_events(ident):
        for recording_url in get_recording_urls(event['url']):
            yield recording_url


def annex_url(url):
    """Annexes the given url.

    :type url: str
    """
    LOGGER.info('Annexing {}'.format(url))
    call(['git-annex', 'addurl', url, '--relaxed',
          '--file={}'.format(url.split('de/')[1])])
    # cuts off the first part to mirror the folder structure of
    # the media server


def main():
    if 1 < len(argv) < 4:
        if argv[1] == 'all':
            for rec in get_recording_urls():
                annex_url(rec)
            return 0
        elif len(argv) == 3 and argv[1] == 'conference':
            for rec in get_conference_recording_urls(argv[2]):
                annex_url(rec)
            return 0
    LOGGER.error('No valid arguments.')
    return 1


if __name__ == "__main__":
    main()
