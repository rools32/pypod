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
from pathlib import Path
import urllib
from collections import OrderedDict
import hashlib
from threading import Lock

import termipod.config as Config
from termipod.backends import get_download_func, DownloadError

# Ordered dict by date, contains file size as value
files = {}
total_file_size = {}

cache_lock = Lock()


def filename_get_path(what, filename=''):
    if filename:
        return Config.get('Global.'+what+'_path')+'/'+filename
    else:
        return Config.get('Global.'+what+'_path')


def item_get_filename(item, what):
    if 'link' in item:  # Medium or Search
        tohash = f'{what}: {item["link"]}'

    else:  # Channel
        tohash = f'{what}: {item["id"]}'

    h = hashlib.sha256(tohash.encode()).hexdigest()

    ext = os.path.splitext(item[what])[1]

    return f'{h}{ext}'


def item_get_cache(item, what, print_infos, check_only=False):
    cache_lock.acquire()
    item_locks = item.setdefault('cache_lock', {})
    item_lock = item_locks.setdefault(what, Lock())
    cache_lock.release()

    with item_lock:
        # Build file list sorted by age
        if what not in files:
            filenames = os.listdir(filename_get_path(what))
            filelist = [(f, os.stat(filename_get_path(what, f)))
                        for f in filenames]
            filelist.sort(key=lambda f: f[1].st_ctime, reverse=True)
            files[what] = OrderedDict((f[0], f[1].st_size) for f in filelist)
            total_file_size[what] = sum(files[what].values())

        if not item[what]:
            return ''

        filename = item_get_filename(item, what)
        filepath = filename_get_path(what, filename)

        url = item[what]

        if not os.path.isfile(filepath):
            if check_only:
                return ''
            if what == 'link':
                dlfunc = get_download_func(item)
                try:
                    dlfunc(url, filepath, print_infos)
                except DownloadError:
                    print_infos('Cannot access to %s' % url, mode='error')
                    return ''

            else:
                try:
                    urllib.request.urlretrieve(url, filepath)
                except urllib.error.URLError:
                    return ''

            file_size = os.stat(filepath).st_size
            files[what][filename] = file_size

            total_file_size[what] += file_size
            max_size = 1024**2*Config.get('Global.'+what+'_max_total_mb')
            while total_file_size[what] > max_size and len(files[what]) > 1:
                f, size = files[what].popitem(last=False)
                try:
                    os.unlink(filename_get_path(what, f))
                    total_file_size[what] -= size
                except OSError:
                    pass

        else:
            files[what].move_to_end(filename)

        if not check_only:
            Path(filepath).touch()

        return filepath
