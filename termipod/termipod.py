#!/usr/bin/env python
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

import argparse
import sys
import os
import fcntl
from sys import stderr

from termipod.itemlist import ItemList
from termipod.ui import UI
from termipod.config import Config
from termipod.database import DataBaseVersionException


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Manage your podcasts in your terminal. '
                    'It handle RSS feeds and also Youtube channels.\n'
                    'When no argument is provided UI is shown.')
    parser.add_argument('-f', type=str, metavar='config_file',
                        help='Alternate configuration file')
    parser.add_argument('--add', type=str, metavar='url',
                        help='Add Youtube channel or RSS feed')
    parser.add_argument(
        '--add-opts', type=str, metavar='options',
        help="""Options given with key=value pair space separated string:
                [count=<count>] [strict[=<0|1>]] [auto[=<regex>]]
                [mask=<regex>] [categories=<category,category>] [force[=<0|1>]]
                [name=<new name>]
        """)
    parser.add_argument(
        '--auto', type=str, nargs=2, metavar=('url', 'pattern'),
        help="Pattern for media to be downloaded automatically "
             "('.*' for all)")
    parser.add_argument(
        '--up', type=str, nargs='?', const=True,  metavar='url',
        help='Update channels and download new videos for channels '
             'maked as auto')
    parser.add_argument('--disable-channel', type=str, metavar='url',
                        help='Disable channel by url')
    parser.add_argument('--remove-channel', type=str, metavar='url',
                        help='Remove channel and media by url')
    parser.add_argument(
        '--export-channels', type=str, nargs='?',
        const=True, metavar='filename',
        help='Export channel list (url and name, one channel by line). '
             'Argument can be followed by filename')
    parser.add_argument('--updatedb', action='store_true',
                        help='Update old database')
    args = parser.parse_args()

    # Init configuration
    config_params = {}
    if args.f:
        config_params['config_path'] = args.f
    config = Config(**config_params)
    os.chdir(config.media_path)

    # Ensure only one instance is running
    instance_file = open('/tmp/termipod.lock', 'w')
    try:
        fcntl.lockf(instance_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print('Termipod already running!')
        exit(1)

    if len(sys.argv) == 1 or (len(sys.argv) == 3 and args.f):
        UI(config)

    else:
        updatedb = True if args.updatedb else False
        try:
            item_list = ItemList(config, print_infos, wait=True,
                                 updatedb=updatedb)
        except DataBaseVersionException as e:
            print(e, file=stderr)
            exit(1)

        if args.add:
            ret = item_list.new_channel(args.add, args.add_opts)
            if not ret:
                sys.exit(-1)

        if args.auto:
            url, auto = args.auto
            item_list.channel_set_auto('cmd', [url], auto)

        if args.up:
            if isinstance(args.up, bool):
                item_list.update_channels('cmd')
            else:
                item_list.update_channels('cmd', [args.up])

        if args.disable_channel:
            item_list.disable_channels('cmd', [args.disable_channel])

        if args.remove_channel:
            item_list.remove_channels('cmd', [args.remove_channel])

        if args.export_channels:
            channels = item_list.export_channels()
            if isinstance(args.export_channels, bool):
                print(channels)
            else:
                print(channels, file=open(args.export_channels, 'w'))


def print_infos(message, *args, **kwargs):
    print(message)


if __name__ == "__main__":
    main()
