# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

import curses
import selectors
import sys
import unicodedata

from .frame import Frame
from .widget import Widget
from .keyinputevent import Key
from .keyinputevent import KeyInputEvent
from .characterinputevent import CharacterInputEvent

class Display (Widget):
    def __init__ (self, selector, screen):
        self.selector = selector
        self.screen = screen
        self.child = None
        self.selector.register (sys.stdin, selectors.EVENT_READ)
        self.screen.nodelay (True)

    def set_child (self, child):
        self.child = child

    def handle_selector_event (self, key, mask):
        if key.fileobj == sys.stdin:
            self.handle_input ()

    def refresh (self):
        (max_lines, max_width) = self.screen.getmaxyx ()
        frame = Frame (max_width, max_lines)
        if self.child is not None:
            self.child.render (frame)

        # FIXME: Only if support colors, otherwise fallback to closest match
        colors = {}
        def get_color (color):
            i = colors.get (color)
            if i is None:
                i = len (colors) + 1
                # FIXME: Validate color
                curses.init_color (i,
                                   1000 * int (color[1:3], 16) // 255,
                                   1000 * int (color[3:5], 16) // 255,
                                   1000 * int (color[5:], 16) // 255)
                colors[color] = i
            return i

        color_pairs = {}
        def get_color_pair (foreground, background):
            i = color_pairs.get ((foreground, background))
            if i is None:
                i = len (color_pairs) + 1
                curses.init_pair (i, get_color (foreground), get_color (background))
                color_pairs[(foreground, background)] = i
            return i

        for y in range (frame.height):
            for x in range (frame.width):
                pixel = frame.buffer[y][x]
                get_color_pair (pixel.foreground, pixel.background)
        for y in range (frame.height):
            text = ''
            current_color = (None, None)
            x = 0
            while x < frame.width:
                pixel = frame.buffer[y][x]
                # FIXME: Can't place in bottom right for some reason
                if y == frame.height - 1 and x == frame.width - 1:
                    break
                c = chr (pixel.character)
                self.screen.addstr (y, x, c, curses.color_pair (get_color_pair (pixel.foreground, pixel.background)))
                if unicodedata.east_asian_width (c) in ('W', 'F'):
                    x += 2
                else:
                    x += 1

        (cursor_y, cursor_x) = frame.cursor
        self.screen.move (cursor_y, cursor_x)
        self.screen.refresh ()

    def handle_input (self):
        while True:
            key = self.screen.getch ()
            if key == -1:
                return
            if key >= 0x20 and key <= 0x7F:
                self.handle_event (CharacterInputEvent (key)) # FIXME: Handle UTF-8
            elif key == ord ('\n'):
                self.handle_event (KeyInputEvent (Key.ENTER))
            elif key == ord ('\t'):
                self.handle_event (KeyInputEvent (Key.TAB))
            elif key == curses.KEY_F1:
                self.handle_event (KeyInputEvent (Key.F1))
            elif key == curses.KEY_F2:
                self.handle_event (KeyInputEvent (Key.F2))
            elif key == curses.KEY_F3:
                self.handle_event (KeyInputEvent (Key.F3))
            elif key == curses.KEY_F4:
                self.handle_event (KeyInputEvent (Key.F4))
            elif key == curses.KEY_F5:
                self.handle_event (KeyInputEvent (Key.F5))
            elif key == curses.KEY_F6:
                self.handle_event (KeyInputEvent (Key.F6))
            elif key == curses.KEY_F7:
                self.handle_event (KeyInputEvent (Key.F7))
            elif key == curses.KEY_F8:
                self.handle_event (KeyInputEvent (Key.F8))
            elif key == curses.KEY_F9:
                self.handle_event (KeyInputEvent (Key.F9))
            elif key == curses.KEY_UP:
                self.handle_event (KeyInputEvent (Key.UP))
            elif key == curses.KEY_DOWN:
                self.handle_event (KeyInputEvent (Key.DOWN))
            elif key == curses.KEY_LEFT:
                self.handle_event (KeyInputEvent (Key.LEFT))
            elif key == curses.KEY_RIGHT:
                self.handle_event (KeyInputEvent (Key.RIGHT))
            elif key == curses.KEY_HOME:
                self.handle_event (KeyInputEvent (Key.HOME))
            elif key == curses.KEY_END:
                self.handle_event (KeyInputEvent (Key.END))
            elif key == curses.KEY_NPAGE:
                self.handle_event (KeyInputEvent (Key.PAGE_DOWN))
            elif key == curses.KEY_PPAGE:
                self.handle_event (KeyInputEvent (Key.PAGE_UP))
            elif key == curses.KEY_BACKSPACE:
                self.handle_event (KeyInputEvent (Key.BACKSPACE))
            elif key == curses.KEY_DC:
                self.handle_event (KeyInputEvent (Key.DELETE))
            elif key == curses.KEY_IC:
                self.handle_event (KeyInputEvent (Key.INSERT))
            else:
                open ('debug.log', 'a').write ('Unknown input {}\n'.format (repr (key)))
