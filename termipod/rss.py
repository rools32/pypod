# -*- coding: utf-8 -*-
#
# termipod
# Copyright (c) 2020 Cyril Bordage
#
# termipod is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# termipod is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from time import mktime
import urllib.request

import feedparser as fp

from termipod.utils import printable_str


def get_all_data(url, opts, print_infos):
    return get_data(url, print_infos)


def get_new_data(channel, opts, print_infos):
    url = channel['url']
    return get_data(url, print_infos)


def get_data(url, print_infos):
    # to avoid using request_headers in fp.parse
    # we use urlopen
    rawpage = urllib.request.urlopen(url).read()
    rss = fp.parse(rawpage)

    feed = rss.feed
    if not feed:
        print_infos('Cannot load '+url)
        return None

    data = {}
    data['url'] = url
    data['title'] = printable_str(feed['title'])
    data['type'] = 'rss'

    data['items'] = []

    try:
        url = feed['image']['href']
        data['thumbnail'] = url
    except KeyError:
        data['thumbnail'] = ''

    entries = rss.entries
    maxtime = 0
    for entry in entries:
        medium = {}
        medium['channel'] = data['title']
        medium['url'] = url
        medium['title'] = printable_str(entry['title'])
        medium['date'] = int(mktime(entry['published_parsed']))
        medium['description'] = entry['summary']
        medium['thumbnail'] = ''

        maxtime = max(maxtime, medium['date'])

        medium['link'] = None
        medium['link_type'] = None  # TODO add in database
        for link in entry['links']:
            if 'medium' in link['type'] or 'audio' in link['type']:
                medium['link'] = link['href']
                medium['link_type'] = link['type']

        if 'itunes_duration' in entry:
            sduration = entry['itunes_duration']
            medium['duration'] = sum([int(x)*60**i for (i, x) in
                                      enumerate(sduration.split(':')[::-1])])
        data['items'].append(medium)

    if 'updated_parsed' in feed:
        data['updated'] = mktime(feed['updated_parsed'])
    else:
        data['updated'] = maxtime

    return data


def download(url, filename, print_infos):
    try:
        urllib.request.urlretrieve(url, filename)
    except urllib.error.URLError:
        print_infos('Cannot access to %s' % url)
        return 1
    else:
        return 0
