#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# termipod
# Copyright (c) 2018 Cyril Bordage
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

from termipod.itemlist import ItemList
from termipod.ui import UI
import termipod.config as config


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Manage your podcasts in your terminal.'
                    'It handle RSS feeds and also Youtube channels.\n'
                    'When no argument is provided UI is shown.')
    parser.add_argument('--add', type=str,
                        help='Add Youtube channel or RSS feed')
    parser.add_argument(
        '--auto', type=str,
        help="Pattern for media to be downloaded automatically ('.*' for all)",
        required='--add' in sys.argv)
    parser.add_argument(
        '--up', action='store_true',
        help='Update channels and download new videos for channel set as auto')
    parser.add_argument('--disable-channel', type=str,
                        help='Disable channel by url')
    parser.add_argument('--remove-channel', type=str,
                        help='Remove channel and media by url')
    args = parser.parse_args()

    if args.auto and not args.add:
        parser.error('with --auto, --add is required')

    os.chdir(config.media_path)

    if len(sys.argv) == 1:
        UI(config)

    else:
        item_list = ItemList(config, wait=True)

        if args.add:
            auto = ''
            if args.auto:
                auto = args.auto
            item_list.new_channel(args.add, auto=auto)
        if args.up:
            item_list.update_medium_list()
        if args.disable_channel:
            item_list.db.channel_disable(args.disable_channel)
        if args.remove_channel:
            item_list.db.channel_remove(args.remove_channel)


if __name__ == "__main__":
    main()
