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

from .frame import Frame
from .container import Container
from .keyinputevent import Key
from .keyinputevent import KeyInputEvent
from .characterinputevent import CharacterInputEvent
from .theme import Theme

class Display (Container):
    def __init__ (self, selector, screen):
        Container.__init__ (self)
        self.selector = selector
        self.screen = screen
        self.child = None
        self.selector.register (sys.stdin, selectors.EVENT_READ)
        self.screen.nodelay (True)
        self.theme = Theme ()

    def set_child (self, child):
        self.child = child

    def handle_selector_event (self, key, mask):
        if key.fileobj == sys.stdin:
            self.handle_input ()

    def refresh (self):
        (max_lines, max_width) = self.screen.getmaxyx ()
        if self.child is not None:
            frame = self.render_child (self.child, max_width, max_lines, self.theme)
        else:
            frame = Frame (max_width, max_lines)

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
            if foreground is None:
                foreground = '#FFFFFF'
            if background is None:
                background = '#000000'
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
                if pixel.character is None:
                    character = ' '
                else:
                    character = pixel.character
                self.screen.addstr (y, x, character, curses.color_pair (get_color_pair (pixel.foreground, pixel.background)))
                if pixel.is_wide ():
                    x += 2
                else:
                    x += 1

        if frame.cursor is None:
            curses.curs_set (0)
        else:
            curses.curs_set (1)
            (cursor_x, cursor_y) = frame.cursor
            cursor_x = min (cursor_x, max_width - 1)
            cursor_y = min (cursor_y, max_lines - 1)
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
            elif key == 0:
                self.handle_event (KeyInputEvent (Key.CTRL_SPACE))
            elif key == 1:
                self.handle_event (KeyInputEvent (Key.CTRL_A))
            elif key == 2:
                self.handle_event (KeyInputEvent (Key.CTRL_B))
            elif key == 3:
                self.handle_event (KeyInputEvent (Key.CTRL_C))
            elif key == 4:
                self.handle_event (KeyInputEvent (Key.CTRL_D))
            elif key == 5:
                self.handle_event (KeyInputEvent (Key.CTRL_E))
            elif key == 6:
                self.handle_event (KeyInputEvent (Key.CTRL_F))
            elif key == 337:
                self.handle_event (KeyInputEvent (Key.SHIFT_UP))
            elif key == 336:
                self.handle_event (KeyInputEvent (Key.SHIFT_DOWN))
            elif key == 393:
                self.handle_event (KeyInputEvent (Key.SHIFT_LEFT))
            elif key == 402:
                self.handle_event (KeyInputEvent (Key.SHIFT_RIGHT))
            elif key == 353:
                self.handle_event (KeyInputEvent (Key.SHIFT_TAB))
            elif key == 530:
                self.handle_event (KeyInputEvent (Key.CTRL_END))
            elif key == 535:
                self.handle_event (KeyInputEvent (Key.CTRL_HOME))
            else:
                open ('debug.log', 'a').write ('Unknown input {}\n'.format (repr (key)))
