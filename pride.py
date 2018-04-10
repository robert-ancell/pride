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

class Frame:
    def __init__ (self, width, height):
        self.width = width
        self.height = height
        self.buffer = []
        for y in range (height):
            self.buffer.append ([' '] * width)

    def clear (self):
        self.fill (0, 0, self.width, self.height, ' ')

    def fill (self, x, y, width, height, value):
        for y_ in range (y, height):
            for x_ in range (x, width):
                self.buffer[y_][x_] = value

    def composite (self, x, y, frame):
        # FIXME: Make SubFrame that re-uses buffer?
        width = min (self.width - x, frame.width)
        height = min (self.height - y, frame.height)
        for y_ in range (height):
            source_line = frame.buffer[y_]
            target_line = self.buffer[y + y_]
            for x_ in range (width):
                target_line[x + x_] = source_line[x_]

    def render_text (self, x, y, text):
        if y >= self.height:
            return
        line = self.buffer[y]
        for (i, c) in enumerate (text):
            if x + i >= self.width:
                return
            line[x + i] = c

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

    def render (self, frame):
        frame.clear ()
        for y in range (frame.height):
            frame.render_text (0, y, '%2d' % (y + 1))
        for (y, line) in enumerate (self.buffer.text.split ('\n')):
            frame.render_text (3, y, line)

    def handle_key (self, key):
        if key == 'KEY_BACKSPACE':
            self.backspace ()
        elif key == 'KEY_DC':
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
        elif len (key) == 1 and ord (key) >= 0x20 and ord (key) <= 0x7E:
            self.insert (key)
        elif len (key) == 1 and ord (key) & 0x80 != 0: # UTF-8
            open ('debug.log', 'a').write ('FIXME: UTF-8\n')
        else:
            open ('debug.log', 'a').write ('Unhandled key {}\n'.format (repr (key)))

class Console:
    def __init__ (self):
        self.pid = 0
        self.cursor = (0, 0)
        self.lines = []

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

        # Process data
        while self.buffer != '':
            c = self.buffer[0]
            #open ('debug.log', 'a').write ('Character {}\n'.format (ord (c)))
            if c == '\033':
                if len (self.buffer) == 1:
                    return
                # ANSI CSI
                if self.buffer[1] == '[':
                    # Find end characters
                    end = 2
                    def is_csi_end (c):
                        n = ord (c)
                        return n >= 0x40 and n <= 0x7F;
                    while end < len (self.buffer) and not is_csi_end (self.buffer[end]):
                        end += 1
                    if end >= len (self.buffer):
                        return # Not got full sequence, wait for more data

                    code = self.buffer[end]
                    params = self.buffer[2:end]
                    #open ('debug.log', 'a').write ('CSI code={} params={}\n'.format (code, params))
                    self.buffer = self.buffer[end + 1:]
                    if code == 'A': # CUU - cursor up
                        count = 1
                        if params != '':
                            count = int (param)
                        self.up (count)
                    elif code == 'B': # CUD - cursor down
                        count = 1
                        if params != '':
                            count = int (param)
                        self.down (count)
                    elif code == 'C': # CUF - cursor right
                        count = 1
                        if params != '':
                            count = int (param)
                        self.right (count)
                    elif code == 'D': # CUB - cursor left
                        count = 1
                        if params != '':
                            count = int (param)
                        self.left (count)
                    elif code == 'H': # CUP - cursor position
                        line = 1
                        col = 1
                        if params != '':
                            args = params.split (';')
                            if len (args) > 0:
                                line = int (args[0])
                            if len (args) > 1:
                                col = int (args[1])
                        self.cursor = (line - 1, col - 1)
                    elif code == 'J': # ED - erase display
                        mode = params
                        if mode == '' or mode == '0': # Erase cursor to end of display
                            open ('debug.log', 'a').write ('Unknown ED mode={}\n'.format (params))
                        elif mode == '1': # Erase from start to cursor (inclusive)
                            open ('debug.log', 'a').write ('Unknown ED mode={}\n'.format (params))
                        elif mode == '2': # Erase whole display
                            self.lines = []
                        else:
                            open ('debug.log', 'a').write ('Unknown ED mode={}\n'.format (params))
                    elif code == 'K': # EL - erase line
                        mode = params
                        if mode == '' or mode == '0':
                            self.erase (self.cursor[1])
                        elif mode == '1':
                            self.erase (0, self.cursor[1])
                        elif mode == '2':
                            self.erase (0)
                        else:
                            open ('debug.log', 'a').write ('Unknown EL mode={}\n'.format (params))
                    elif code == 'P': # DCH - delete characters
                        count = 1
                        if params != '':
                            count = int (params)
                        self.erase (self.cursor[1], self.cursor[1] + count);
                    else:
                        open ('debug.log', 'a').write ('Unknown CSI code={} params={}\n'.format (code, params))
                else:
                    # FIXME
                    open ('debug.log', 'a').write ('Unknown escape code {}\n'.format (ord (c)))
                    self.buffer = self.buffer[1:]
            elif c == '\b': # BS
                self.left (1)
                self.buffer = self.buffer[1:]
            elif c == '\a': # BEL
                # FIXME: Flash bell symbol or similar?
                self.buffer = self.buffer[1:]
            elif c == '\r': # CR
                self.cursor = (self.cursor[0], 0)
                self.buffer = self.buffer[1:]
            elif c == '\n': # LF
                self.cursor = (self.cursor[0] + 1, 0)
                self.buffer = self.buffer[1:]
            elif ord (c) >= 0x20 and ord (c) <= 0x7E:
                self.insert (c)
                self.buffer = self.buffer[1:]
            elif ord (c) & 0x80 != 0: # UTF-8
                open ('debug.log', 'a').write ('FIXME: UTF-8\n')
            else:
                open ('debug.log', 'a').write ('Unknown character {}\n'.format (ord (c)))
                self.buffer = self.buffer[1:]

    def left (self, count):
        count = min (count, self.cursor[1])
        self.cursor = (self.cursor[0], self.cursor[1] - count)

    def right (self, count):
        #FIXME: count = min (count, width - cursor[1])
        self.cursor = (self.cursor[0], self.cursor[1] + count)

    def up (self, count):
        count = min (count, self.cursor[0])
        self.cursor = (self.cursor[0] - count, self.cursor[1])

    def down (self, count):
        #FIXME: count = min (count, height - cursor[0])
        self.cursor = (self.cursor[0] + count, self.cursor[1])

    # Ensure line exists to current cursor position
    def ensure_line (self):
        row = self.cursor[0]
        while len (self.lines) <= row:
            self.lines.append ('')
        while len (self.lines[row]) < self.cursor[1]:
            self.lines[row] += ' '

    def erase (self, start, end = -1):
        self.ensure_line ()
        row = self.cursor[0]
        col = self.cursor[1]
        line = self.lines[row]
        self.lines[row] = line[:start]
        if end >= 0:
            self.lines[row] += line[end:]

    def insert (self, text):
        self.ensure_line ()
        row = self.cursor[0]
        col = self.cursor[1]
        line = self.lines[row]
        self.lines[row] = line[:col] + text + line[col + len (text):]
        self.cursor = (self.cursor[0], self.cursor[1] + len (text))

    def get_cursor (self):
        return self.cursor

    def render (self, frame):
        frame.clear ()
        for (y, line) in enumerate (self.lines):
            frame.render_text (0, y, line)

    def handle_key (self, key):
        if len (key) == 1:
            os.write (self.fd, key.encode ('utf-8'))
        elif key == 'KEY_BACKSPACE':
            os.write (self.fd, '\b'.encode ('ascii'))
        elif key == 'KEY_DC':
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
        frame = Frame (max_width, max_lines)
        self.render (frame)
        for y in range (frame.height):
            text = ''
            for x in range (frame.width):
                text += frame.buffer[y][x]
            if y == frame.height - 1:
                text = text[:-1]
            self.screen.addstr (y, 0, text)

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

    def render (self, frame):
        editor_height = frame.height // 2
        console_height = frame.height - editor_height - 1

        editor_frame = Frame (frame.width, editor_height)
        self.view.render (editor_frame)
        console_frame = Frame (frame.width, console_height)
        self.console.render (console_frame)

        frame.composite (0, 0, editor_frame)
        frame.render_text (0, editor_height, 'X' * frame.width)
        frame.composite (0, editor_height + 1, console_frame)

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
