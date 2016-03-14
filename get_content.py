#!/usr/bin/env python3
# Author: Nelo-T. Wallus <nelo@wallus.de>
import json
import requests
import logging
import os.path as path
from sys import argv
from subprocess import call

API_SERVER = 'http://api.media.ccc.de/'
API_PATH = {
    'conferences': '/public/conferences',
    'conference': '/public/conferences/',
    'event': '/public/events/',
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
        assert key_or_url in API_PATH.keys(), 'Invalid keyword {}'.format(key_or_url)
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


def get_conferences():
    """Generator, yields json dicts of the conferences.

    :rtype: dict
    """
    for conference in request('conferences')['conferences']:
        yield conference


def get_conference_url(name):
    """Returns the url of a conference. Expects the acronym.

    :type name: str
    :rtype: str
    """
    for conference in get_conferences():
        if conference['acronym'] == name:
            return conference['url']


def print_conferences():
    """Lists conferences with acronym and id."""
    for conference in get_conferences():
        ident = conference['url'].split('/')[-1]
        acronym = conference['acronym']
        title = conference['title']
        print("{:5}\t{:35}\t{}".format(ident, acronym, title))


def annex_url(url):
    """Annexes the given url.

    :type url: str
    """
    LOGGER.info('Annexing {}'.format(url))
    filename = url.split('de/')[1]
    if not path.isfile(filename):
        call(['git-annex', 'addurl', url, '--relaxed',
              '--file={}'.format(filename)])
        call(['git-annex', 'addurl', url + '.torrent', '--relaxed',
              '--file={}'.format(filename)])


def main():
    if len(argv) == 1 or argv[1] == 'help':
        def printh(subcommand, explanation):
            print("\t{} {}".format(argv[0], subcommand))
            print("\t\t" + explanation)
        print("Usage: ")
        printh("all", "annex all media on media.ccc.de")
        printh("lookup acronym", "lookup url of a conference using acronym")
        printh("list", "list all available conferences on media.ccc.de in formatted output")
        printh("conference id", "annex all media from conference using id")
        return 0
    elif argv[1] == 'all':
        for rec in get_recording_urls():
            annex_url(rec)
        return 0
    elif argv[1] == 'lookup':
        if argv[2]:
            print(get_conference_url(argv[2]))
        return 0
    elif argv[1] == 'list':
        print_conferences()
        return 0
    elif len(argv) == 3 and argv[1] == 'conference':
        for rec in get_conference_recording_urls(argv[2]):
            annex_url(rec)
        return 0
    LOGGER.error('No valid arguments.')
    return 1


if __name__ == "__main__":
    main()
