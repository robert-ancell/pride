#!/usr/bin/python3

# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

import sys
import os
import curses
import selectors
import pty
import subprocess
import signal

class TextBuffer:
    def __init__ (self):
        self.text = ''

    def insert (self, index, text):
        self.text = self.text[:index] + text + self.text[index:]

    def delete (self, index, count):
        self.text = self.text[:index] + self.text[index + count:]

class TextView:
    def __init__ (self, buffer):
        self.buffer = buffer
        self.cursor = 0

    def insert (self, text):
        self.buffer.insert (self.cursor, text)
        self.cursor += len (text)

    def backspace (self):
        if self.cursor == 0:
            return
        self.buffer.delete (self.cursor - 1, 1)
        self.cursor -= 1

    def delete (self):
        self.buffer.delete (self.cursor, 1)

    def left (self):
        self.cursor -= 1

    def right (self):
        if self.cursor < len (self.buffer.text):
            self.cursor += 1

    def up (self):
        while self.cursor > 0:
            self.cursor -= 1
            if self.buffer.text[self.cursor] == '\n':
                return

    def down (self):
        while self.cursor < len (self.buffer.text):
            self.cursor += 1
            if self.cursor == len (self.buffer.text) or self.buffer.text[self.cursor] == '\n':
                return

    def home (self):
        while self.cursor > 0:
            if self.buffer.text[self.cursor - 1] == '\n':
                return
            self.cursor -= 1

    def end (self):
        while self.cursor < len (self.buffer.text):
            if self.buffer.text[self.cursor] == '\n':
                return
            self.cursor += 1

    def get_cursor (self):
        line = 0
        offset = 0
        have_offset = False
        c = self.cursor
        while c > 0:
            c -= 1
            if self.buffer.text[c] == '\n':
                line += 1
                have_offset = True
            if not have_offset:
                offset += 1
        return (line, offset)

    def render (self, width, height):
        lines = []
        offset = 0
        for line in range (height):
            text = '%2d ' % line
            while offset < len (self.buffer.text):
                if self.buffer.text[offset] == '\n':
                    offset += 1
                    break
                text += self.buffer.text[offset]
                offset += 1
            while len (text) < width:
                text += ' '
            lines.append (text[:width])
        return lines

    def handle_key (self, key):
        if key == 'KEY_BACKSPACE':
            self.backspace ()
        elif key == 'KEY_DELETE':
            self.delete ()
        elif key == 'KEY_LEFT':
            self.left ()
        elif key == 'KEY_RIGHT':
            self.right ()
        elif key == 'KEY_UP':
            self.up ()
        elif key == 'KEY_DOWN':
            self.down ()
        elif key == 'KEY_HOME':
            self.home ()
        elif key == 'KEY_END':
            self.end ()
        elif key == '\t':
            self.insert ('    ')
        elif len (key) == 1:
            self.insert (key)

class Console:
    def __init__ (self):
        self.pid = 0
        self.cursor = (0, 0)

    def run (self, args):
        self.buffer = ''
        if self.pid != 0:
            os.kill (self.pid, signal.SIGTERM)
        (self.pid, self.fd) = pty.fork ()
        if self.pid == 0:
            subprocess.run (args)
            exit ()

    def read (self):
        try:
            self.buffer += os.read (self.fd, 65535).decode ('utf-8')
        except:
            os.close (self.fd)

    def get_cursor (self):
        return (0, 0) # FIXME

    def render (self, width, height):
        lines = []
        offset = 0
        for line in range (height):
            text = ''
            while offset < len (self.buffer):
                if self.buffer[offset] == '\r':
                    offset += 1
                    continue
                if self.buffer[offset] == '\n':
                    offset += 1
                    break
                text += self.buffer[offset]
                offset += 1
            while len (text) < width:
                text += ' '
            lines.append (text[:width])
        return lines

    def handle_key (self, key):
        if len (key) == 1:
            os.write (self.fd, key.encode ('utf-8'))
        elif key == 'KEY_BACKSPACE':
            os.write (self.fd, '\b'.encode ('ascii'))
        elif key == 'KEY_DELETE':
            os.write (self.fd, '\033[3~'.encode ('ascii'))
        elif key == 'KEY_UP':
            os.write (self.fd, '\033[A'.encode ('ascii'))
        elif key == 'KEY_DOWN':
            os.write (self.fd, '\033[B'.encode ('ascii'))
        elif key == 'KEY_RIGHT':
            os.write (self.fd, '\033[C'.encode ('ascii'))
        elif key == 'KEY_LEFT':
            os.write (self.fd, '\033[D'.encode ('ascii'))
        elif key == 'KEY_HOME':
            os.write (self.fd, '\033[H'.encode ('ascii'))
        elif key == 'KEY_END':
            os.write (self.fd, '\033[F'.encode ('ascii'))

class Pride:
    def __init__ (self, screen):
        self.screen = screen
        self.sel = selectors.DefaultSelector ()
        self.buffer = TextBuffer ()
        self.view = TextView (self.buffer)
        self.console = Console ()
        self.console_focus = False

    def run (self):
        self.sel.register (sys.stdin, selectors.EVENT_READ)
        try:
            self.buffer.text = open ('main.py').read ()
        except:
            pass
        self.console.run (['python3'])
        self.sel.register (self.console.fd, selectors.EVENT_READ)

        self.refresh ()
        while True:
            events = self.sel.select ()
            for key, mask in events:
                if key.fileobj == sys.stdin:
                    key = self.screen.getkey ()
                    self.handle_key (key)
                elif key.fd == self.console.fd:
                    self.console.read ()
            self.refresh ()

    def refresh (self):
        (max_lines, max_width) = self.screen.getmaxyx ()
        lines = self.render (max_width, max_lines)
        for (line, text) in enumerate (lines):
            trim = 0 # FIXME: Can't set lower right for some reason...
            if line == max_lines - 1:
                trim = 1
            self.screen.addstr (line, 0, text[:max_width - trim])

        if self.console_focus:
            (cursor_y, cursor_x) = self.console.get_cursor ()
            cursor_y += max_lines // 2 + 1
        else:
            (cursor_y, cursor_x) = self.view.get_cursor ()
            cursor_x += 3
        self.screen.move (cursor_y, cursor_x)
        self.screen.refresh ()

    def run_program (self):
        open ('main.py', 'w').write (self.buffer.text)
        if self.console.pid != 0:
            self.sel.unregister (self.console.fd)
        self.console.run (['python3', 'main.py'])
        self.sel.register (self.console.fd, selectors.EVENT_READ)

    def render (self, width, height):
        editor_height = height // 2
        console_height = height - editor_height - 1

        # FIXME: Render into buffer
        view_lines = self.view.render (width, editor_height)
        console_lines = self.console.render (width, console_height)

        return view_lines + ['X' * width] + console_lines

    def handle_key (self, key):
        if key == 'KEY_F(4)':
            self.console_focus = not self.console_focus
        elif key == 'KEY_F(5)':
            self.run_program ()
        elif self.console_focus:
            self.console.handle_key (key)
        else:
            self.view.handle_key (key)

def main (screen):
    pride = Pride (screen)
    pride.run ()

curses.wrapper (main)
