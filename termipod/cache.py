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
import os
import os.path
import urllib
from collections import OrderedDict
import hashlib

import termipod.config as Config

# Ordered dict by date, contains file size as value
files = None
total_file_size = 0


def filename_get_path(what, filename=''):
    if filename:
        return Config.get_path(what)+'/'+filename
    else:
        return Config.get_path(what)


def item_get_filename(item, what):
    if 'channel' in item:  # Medium
        tohash = f'{what}: {item["cid"]} {item["link"]}'

    else:  # Channel
        tohash = f'{what}: {item["id"]}'

    h = hashlib.sha256(tohash.encode()).hexdigest()

    ext = os.path.splitext(item[what])[1]

    return f'{h}{ext}'


def item_get_cache(item, what, print_infos):
    global files, total_file_size
    # Build file list sorted by age
    if files is None:
        filenames = os.listdir(filename_get_path(what))
        filelist = [(f, os.stat(filename_get_path(what, f)))
                    for f in filenames]
        filelist.sort(key=lambda f: f[1].st_ctime, reverse=True)
        files = OrderedDict((f[0], f[1].st_size) for f in filelist)
        total_file_size = sum(files.values())

    if not item[what]:
        return ''

    filename = item_get_filename(item, what)
    filepath = filename_get_path(what, filename)

    url = item[what]

    if not os.path.isfile(filepath):
        try:
            urllib.request.urlretrieve(url, filepath)
            file_size = os.stat(filepath).st_size
            files[filename] = file_size

            total_file_size += file_size
            max_size = 1024**2*Config.get_size(what)
            while total_file_size > max_size and len(files) > 1:
                f, size = files.popitem(last=False)
                try:
                    os.unlink(filename_get_path(what, f))
                except OSError:
                    pass
                total_file_size -= size

        except urllib.error.URLError:
            print_infos('Cannot access to %s' % url, mode='error')
            return ''

    else:
        files.move_to_end(filename)

    return filepath
