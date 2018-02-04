import curses
import curses.textpad
import shlex

from utils import durationToStr, tsToDate, printLog, formatString
from itemlist import ItemList
from keymap import getAction, mapToHelp

class UI():
    def __init__(self, dbName):
        screen = curses.initscr()
        height,width = screen.getmaxyx()
        #printLog('Height: %d, Width: %d' % (height, width))
        screen.immedok(True)
        curses.start_color()
        curses.curs_set(0) # disable cursor
        curses.cbreak() # no need to press enter to react to keys
        curses.noecho() # do not show pressed keys
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        screen.refresh()

        self.statusArea = StatusArea(screen)
        self.itemList = ItemList(dbName, self.printInfos)

        tabs = Tabs(screen, self.itemList, self.printInfos)

        # New tabs
        tabs.addVideos('remote', 'Remote videos')
        tabs.addVideos('local', 'Playlist')
        tabs.addVideos('download', 'Downloading')
        tabs.addChannels('channels', 'Channels')
        tabs.showTab(0)

        while True:
            # Wait for key
            key = screen.getch()
            area = tabs.getCurrentArea()

            areaKeyClass = area.getKeyClass()
            idx = area.getIdx()

            action = getAction(areaKeyClass, key)
            printLog(action)

            if None == action:
                self.printInfos('Key %s not mapped for keyClass %s' %
                        (str(key), areaKeyClass))

            ####################################################################
            # All tab commands
            ####################################################################

            elif 'line_down' == action:
                tabs.moveScreen('line', 'down')
            elif 'line_up' == action:
                tabs.moveScreen('line', 'up')
            elif 'page_down' == action:
                tabs.moveScreen('page', 'down')
            elif 'page_up' == action:
                tabs.moveScreen('page', 'up')
            elif 'bottom' == action:
                tabs.moveScreen('all', 'down')
            elif 'top' == action:
                tabs.moveScreen('all', 'up')

            elif 'screen_infos' == action:
                tabs.screenInfos()

            elif 'tab_next' == action:
                tabs.showNextTab()

            elif 'tab_prev' == action:
                tabs.showNextTab(reverse=True)

            elif 'help' == action:
                area.showHelp()

            elif 'infos' == action:
                area.showInfos()

            elif 'command_get' == action:
                string = self.statusArea.runCommand(':')
                command = shlex.split(string)
                self.printInfos('Run: '+str(command))
                if command[0] in ('q', 'quit'):
                    exit()
                elif command[0] in ('h', 'help'):
                    self.printInfos('Help!!!!!!')
                elif command[0] in ('add',):
                    if 1 == len(command):
                        addHelp = 'Usage: add url [auto] [genre]'
                        self.printInfos(addHelp)
                    else:
                        self.itemList.addChannel(*command[1:])

            elif 'search_get' == action:
                searchString = self.statusArea.runCommand('/')
                self.printInfos('Search: '+searchString)
                tabs.highlight(searchString)
            elif 'search_next' == action:
                tabs.nextHighlight()
            elif 'search_prev' == action:
                tabs.nextHighlight(reverse=True)

            elif 'quit' == action:
                break

            elif 'select_item' == action:
                tabs.selectItem()
            elif 'select_until' == action:
                tabs.selectUntil()
            elif 'select_clear' == action:
                tabs.selectClear()

            ####################################################################
            # Allvideos commands
            ####################################################################
            # Highlight channel name
            elif 'search_channel' == action:
                channel = area.getCurrentChannel()
                self.printInfos('Search: '+channel)
                tabs.highlight(channel)

            elif 'video_play' == action:
                self.itemList.play(idx)

            elif 'video_playadd' == action:
                self.itemList.playadd(idx)

            elif 'video_stop' == action:
                self.itemList.stop()

            elif 'video_remove' == action:
                # TODO if is being played: self.itemList.stop()
                self.itemList.remove(idx)
                self.itemList.updateVideoAreas()

            elif 'channel_filter' == action:
                tabs.channelFilterSwitch()

            elif 'state_filter' == action:
                tabs.stateSwitch()

            elif 'video_read' == action:
                if 0 == len(area.userSelection):
                    self.itemList.switchRead([idx])
                else:
                    self.itemList.switchRead(area.userSelection)
                    area.userSelection = []

            ####################################################################
            # Remote video commands
            ####################################################################
            elif 'video_download' == action:
                if not len(area.userSelection):
                    self.itemList.download([idx])
                else:
                    self.itemList.download(area.userSelection)
                    area.userSelection = []

            elif 'video_update' == action:
                updated = self.itemList.updateVideoList()

            ####################################################################
            # Local video commands
            ####################################################################

            ####################################################################
            # Downloading video commands
            ####################################################################

            ####################################################################
            # Channel commands
            ####################################################################
            elif 'channel_auto' == action:
                self.itemList.channelAuto(idx)

            elif 'channel_auto_custom' == action:
                auto = self.statusArea.runCommand('auto: ')
                self.itemList.channelAuto(idx, auto)

            elif 'channel_show_videos' == action:
                channel = self.itemList.channels[idx]
                self.itemList.channelAuto(idx)
                tabs.showTab('remote')
                tabs.channelFilterSwitch(channel['title'])

    def printInfos(self, string):
        self.statusArea.print(string)

class Tabs:
    def __init__(self, screen, itemList, printInfos):
        self.screen = screen
        self.itemList = itemList
        self.printInfos = printInfos
        self.currentIdx = -1
        self.areas = []
        self.titleArea = TitleArea(screen, '')

    def getAreaIdx(self, name):
        for idx, area in enumerate(self.areas):
            printLog(area.name)
            if name == area.name:
                return idx
        return None

    def addVideos(self, location, name):
        area = VideoArea(self.screen, location, self.itemList.videos, name,
                self.titleArea, self.printInfos)
        self.areas.append(area)
        self.itemList.videoAreas.append(area)

    def addChannels(self, name, displayName):
        area = ChannelArea(self.screen, self.itemList.channels, name,
                displayName, self.titleArea, self.printInfos)
        self.areas.append(area)
        self.itemList.channelAreas.append(area)

    def getCurrentArea(self):
        return self.getArea(self.currentIdx)

    def getArea(self, idx):
        return self.areas[idx]

    def showTab(self, target):
        if str == type(target):
            printLog(target)
            idx = self.getAreaIdx(target)
        else:
            idx = target

        # Hide previous tab
        if -1 != self.currentIdx:
            self.getCurrentArea().shown = False

        self.currentIdx = idx
        area = self.getArea(idx)
        self.titleArea = TitleArea(self.screen, area.getTitleName())
        area.display(True)

    def showNextTab(self, reverse=False):
        if reverse:
            way = -1
        else:
            way = 1
        self.showTab((self.currentIdx+1*way)%len(self.areas))

    def moveScreen(self, what, way):
        area = self.getCurrentArea()
        area.moveScreen(what, way)

    def highlight(self, searchString):
        area = self.getCurrentArea()
        area.highlight(searchString)

    def channelFilterSwitch(self, channel=None):
        area = self.getCurrentArea()
        area.channelFilterSwitch(channel)

    def stateSwitch(self):
        area = self.getCurrentArea()
        area.switchState()

    def screenInfos(self):
        area = self.getCurrentArea()
        area.screenInfos()

    def nextHighlight(self, reverse=False):
        area = self.getCurrentArea()
        area.nextHighlight(reverse)

    def selectItem(self):
        area = self.getCurrentArea()
        area.addToUserSelection()

    def selectUntil(self):
        area = self.getCurrentArea()
        area.addUntilToUserSelection()

    def selectClear(self):
        area = self.getCurrentArea()
        area.clearUserSelection()

    def getCurrentLine(self):
        area = self.getCurrentArea()
        return area.getCurrentLine()

class ItemArea:
    def __init__(self, screen, items, name, displayName, titleArea, printInfos):
        self.printInfos = printInfos
        self.screen = screen
        self.titleArea = titleArea
        height, width = screen.getmaxyx()
        self.height = height-2
        self.width = width-1
        self.name = name
        self.displayName = displayName
        self.win = curses.newwin(self.height+1, self.width, 1, 0)
        self.win.bkgd(curses.color_pair(2))
        self.win.keypad(1) # to handle special keys as one key
        self.highlightOn = False
        self.highlightString = None
        self.oldCursor = 0
        self.cursor = 0
        self.firstLine = 0
        self.content = None
        self.shown = False
        self.items = items
        self.selection = []
        self.userSelection = []

    def addToUserSelection(self, idx=None):
        if None == idx:
            idx = self.getIdx()

        if idx in self.userSelection:
            self.userSelection.remove(idx)
        else:
            self.userSelection.append(idx)

    def addUntilToUserSelection(self):
        idx = self.getIdx()
        if idx < self.userSelection[-1]:
            step = -1
        else:
            step = 1

        start = self.selection.index(self.userSelection[-1])
        end = self.selection.index(idx)

        for i in range(start, end, step):
            sel = self.selection[i+step]
            self.addToUserSelection(sel)

        self.display(redraw=True)
        printLog(self.userSelection)

    def clearUserSelection(self):
        self.userSelection = []
        self.display(redraw=True)

    def resetContent(self):
        self.content = None
        if self.shown:
            self.display(True)

    def updateContent(self, items=None):
        # Rebuild
        if None == items or None == self.content:
            items = self.getSelection()
            self.content = self.itemsToString(items)
            return True
        # Update
        else:
            items = self.getSelection(items)
            self.content[0:0] = self.itemsToString(items)
            return False

    def itemsToString(self, channels):
        return list(map(lambda x: self.itemToString(x, self.width), channels))

    def screenInfos(self):
        line = self.firstLine+self.cursor+1
        total = len(self.selection)
        self.printInfos('%d/%d' % (line, total))

    def getIdx(self):
        if len(self.selection):
            return self.selection[self.firstLine+self.cursor]
        else:
            return -1

    def getCurrentItem(self):
        return self.items[self.getIdx()]

    def getCurrentLine(self):
        return self.content[self.firstLine+self.cursor]

    def highlight(self, string):
        self.highlightOn = True
        self.highlightString = string
        self.display(redraw=True)
        self.nextHighlight()

    def nextHighlight(self, reverse=False):
        if None == self.highlightString:
            return

        itemIdx = None
        if not reverse:
            for i in range(self.firstLine+self.cursor+1, len(self.content)):
                if self.highlightString in self.content[i]:
                    itemIdx = i
                    break
        else:
            for i in range(self.firstLine+self.cursor-1, -1, -1):
                if self.highlightString in self.content[i]:
                    itemIdx = i
                    break

        if None != itemIdx:
            self.moveCursor(itemIdx)

    def noHighlight(self):
        self.highlightOn = False
        self.display(redraw=True)

    def moveCursor(self, itemIdx):
        self.moveScreen('line', 'down', itemIdx-self.cursor-self.firstLine)

    def printLine(self, line, string, bold=False):
        normalStyle = curses.color_pair(2)
        boldStyle = curses.color_pair(1)
        selectStyle = curses.color_pair(3)
        highlightStyle = curses.color_pair(4)
        self.win.move(line, 0)
        self.win.clrtoeol()
        style = None
        if bold:
            self.win.addstr(line, 0, string, boldStyle)
        else:
            # If line is in user selection
            if self.selection[line+self.firstLine] in self.userSelection:
                self.win.addstr(line, 0, string, selectStyle)

            elif self.highlightOn:
                styles = (normalStyle, highlightStyle)

                # Split with highlight string and put it back
                parts = string.split(self.highlightString)
                missingStrings = [self.highlightString]*len(parts)
                parts = [val for pair in zip(parts, missingStrings)
                        for val in pair][:-1]

                written = 0
                styleIdx = 0
                for part in parts:
                    self.win.addstr(line, written, part, styles[styleIdx])
                    written += len(part)
                    styleIdx = (styleIdx+1)%2
            else:
                self.win.addstr(line, 0, string, normalStyle)

    def showHelp(self):
        lines = mapToHelp(self.keyClass)
        PopupArea(self.screen, (self.height, self.width), lines, self.cursor)
        self.display(redraw=True)

    def showInfos(self):
        item = self.getCurrentItem()
        lines = self.itemToString(item, multiLines=True)

        PopupArea(self.screen, (self.height, self.width), lines, self.cursor)
        self.display(redraw=True)

    def positionToIdx(self, firstLine, cursor):
        return firstLine+cursor

    def idxToPosition(self, idx):
        firstLine = int(idx/self.height)*self.height
        cursor = idx-firstLine
        return (firstLine, cursor)

    def moveScreen(self, what, way, number=1):
        redraw = False
        # Move one line down
        idx = self.positionToIdx(self.firstLine, self.cursor)
        if what == 'line' and way == 'down':
            # More lines below
            idx += number
        # Move one line up
        elif what == 'line' and way == 'up':
            # More lines above
            idx -= number
        # Move one page down
        elif what == 'page' and way == 'down':
            idx += self.height*number
        # Move one page up
        elif what == 'page' and way == 'up':
            idx -= self.height*number
        elif what == 'all' and way == 'up':
            idx = 0
        elif what == 'all' and way == 'down':
            idx = len(self.content)-1

        if 0 > idx:
            idx = 0
        elif len(self.content) <= idx:
            idx = len(self.content)-1

        firstLine, cursor = self.idxToPosition(idx)

        # If first line is not the same: we redraw everything
        if (firstLine != self.firstLine):
            redraw = True

        self.oldCursor = self.cursor
        self.cursor = cursor
        self.firstLine = firstLine

        self.display(redraw)

    def resetDisplay(self):
        self.oldCursor = 0
        self.cursor = 0
        self.firstLine = 0
        self.display(True)

    def display(self, redraw=False):
        self.shown = True
        # If new content, we need to check cursor is still valid and set it on
        # the same line if possible
        if None == self.content:
            redraw = self.updateContent()

        # We draw all the page (shift)
        if redraw == True:
            self.userSelection = [] # reset user selection

            for lineNumber in range(self.height):
                if self.firstLine+lineNumber < len(self.content):
                    line = self.content[self.firstLine+lineNumber]
                    # Line where cursor is, bold
                    if lineNumber == self.cursor:
                        self.printLine(lineNumber, line, True)
                    else:
                        self.printLine(lineNumber, line)
                # Erase previous text for empty lines (bottom of scroll)
                else:
                    self.win.move(lineNumber, 0)
                    self.win.clrtoeol()

        elif self.oldCursor != self.cursor:
            self.printLine(self.oldCursor, self.content[self.firstLine+self.oldCursor])
            self.printLine(self.cursor, self.content[self.firstLine+self.cursor], True)
        self.win.refresh()

    def getKeyClass(self):
        return self.keyClass

class VideoArea(ItemArea):
    def __init__(self, screen, location, items, name, titleArea, printInfos):
        super().__init__(screen, items, location, name, titleArea, printInfos)
        self.location = location
        self.state = 'unread'
        self.keyClass = 'videos_'+location
        self.channelFilter = False

    def getTitleName(self):
        return '%s (%s)' % (self.displayName, self.state)

    def extractChannelName(self, line):
        return line.split(u" \u2022 ")[1]

    def getCurrentChannel(self):
        line = self.getCurrentLine()
        return self.extractChannelName(line)

    def channelFilterSwitch(self, channel=None):
        if None == channel and False != self.channelFilter:
            self.channelFilter = False
        else:
            if None == channel:
                channel = self.getCurrentChannel()
            self.channelFilter = channel

        # Update screen
        self.resetContent()

    def switchState(self):
        states = ['all', 'unread', 'read']
        idx = states.index(self.state)
        self.state = states[(idx+1)%len(states)]
        self.printInfos('Show %s videos' % self.state)
        self.titleArea.print(self.getTitleName())
        self.resetContent()

    # if newItems update selection (do not replace)
    def getSelection(self, newItems=None):
        if None == newItems:
            replace = True
            newItems = self.items
        else:
            replace = False
            oldSelection = self.selection

        self.selection = []
        items = []

        for index, item in enumerate(newItems):
            if self.channelFilter and self.channelFilter != item['channel']:
                continue
            if self.location != item['location']:
                continue
            if 'all' != self.state and self.state != item['state']:
                continue

            self.selection.append(index)
            items.append(item)

        if not replace:
            shift = len(newItems)
            oldSelection = [ s+shift for s in oldSelection ]
            self.userSelection = [ s+shift for s in self.userSelection ]
            self.selection += oldSelection
            self.firstLine += len(items)

        return items

    def itemToString(self, item, width=0, multiLines=False):
        formattedItem = dict(item)
        formattedItem['date'] = tsToDate(item['date'])
        formattedItem['duration'] = durationToStr(item['duration'])
        separator = u" \u2022 "

        if not multiLines:
            string = formattedItem['date']
            string += separator
            string += formattedItem['channel']
            string += separator
            string += formattedItem['title']

            string = formatString(string,
                    width-len(separator+formattedItem['duration']))
            string += separator
            string += formattedItem['duration']

        else:
            fields = ['title', 'channel', 'date', 'duration', 'filename']
            string = []
            for f in fields:
                s = '%s%s: %s' % (separator, f, formattedItem[f])
                string.append(s)

        return string

class ChannelArea(ItemArea):
    def __init__(self, screen, items, name, displayName, titleArea, printInfos):
        super().__init__(screen, items, name, displayName, titleArea,
                printInfos)
        self.keyClass = 'channels'

    def getTitleName(self):
        return self.displayName

    def getSelection(self):
        # TODO add filter
        self.selection = []
        items = []
        for index, channel in enumerate(self.items):
            self.selection.append(index)
            items.append(channel)
        return items

    def itemToString(self, channel, width):
        date = tsToDate(channel['updated'])
        newElements = 2 # TODO
        totalElements = 10 # TODO
        separator = u" \u2022 "

        # TODO format and align
        string = channel['title']
        string += separator
        string += channel['type']
        string += separator
        string += '%d/%d' % (newElements, totalElements)
        string += separator
        string += channel['genre']
        string += separator
        string += channel['auto']
        string += separator
        string += date

        return string

class TitleArea:
    def __init__(self, screen, title):
        height, width = screen.getmaxyx()
        self.height = 1
        self.width = width-1
        self.win = curses.newwin(self.height, self.width, 0, 0)
        self.win.bkgd(curses.color_pair(3))
        self.win.keypad(1)
        self.print(title)

    def print(self, string):
        self.win.move(0, 0)
        self.win.clrtoeol()
        self.win.addstr(0, 0, str(string))
        self.win.refresh()

class StatusArea:
    def __init__(self, screen):
        height, width = screen.getmaxyx()
        self.height = 1
        self.width = width-1
        self.win = curses.newwin(self.height, self.width, height-1, 0)
        self.win.bkgd(curses.color_pair(3))
        self.win.keypad(1)
        self.print('')

    def print(self, value):
        string = str(value)
        printLog(string)
        if len(string)+1 > self.width:
            shortString = string[:self.width-4]+'.'*3
        else:
            shortString = string

        self.win.move(0, 0)
        self.win.clrtoeol()
        self.win.addstr(0, 0, str(shortString))
        self.win.refresh()

    def runCommand(self, prefix):
        self.print(prefix)
        #curses.curs_set(2)
        tb = curses.textpad.Textbox(self.win)
        string = tb.edit()[len(prefix):-1] # remove prefix and last char
        return string

class PopupArea:
    def __init__(self, screen, areaSize, rawLines, base, margin=5):
        screenHeight, screenWidth = areaSize

        self.outerMargin = margin
        self.innerMargin = 2
        self.width = screenWidth-self.outerMargin*2
        self.textWidth = self.width-self.innerMargin*2

        lines = []
        for l in rawLines:
            lines.extend(formatString(l, self.textWidth, truncate=False))

        self.height = len(lines)+2 # for border

        # Compute first line position
        if self.height > screenHeight-2:
            printLog('TODO: implement scrollable popup')
            exit(1) # TODO
        start = max(1, base-int(len(lines)/2))
        if start+self.height > screenHeight-1:
            start = screenHeight-1-self.height

        self.win = curses.newwin(self.height, self.width, start,
                self.outerMargin)
        self.win.bkgd(curses.color_pair(3))
        self.win.keypad(1)
        self.win.border('|', '|', '-', '-', '+', '+', '+', '+')

        for line in range(1, 1+len(lines)):
            self.win.move(line, self.innerMargin)
            self.win.clrtoeol()
            self.win.addstr(line, self.innerMargin, str(lines[line-1]))
        self.win.refresh()

        key = screen.getch()
        curses.ungetch(key)
