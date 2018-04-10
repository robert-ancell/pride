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
        self.lines = []

    def clear (self):
        self.lines = []

    # Ensure lines exists to requested position
    def ensure_line (self, x, y):
        while len (self.lines) <= y:
            self.lines.append ('')
        while len (self.lines[y]) < x:
            self.lines[y] += ' '

    def get_line_length (self, y):
        if y >= len (self.lines):
            return 0
        return len (self.lines[y])

    def insert (self, x, y, text):
        self.ensure_line (x, y)
        line = self.lines[y]
        self.lines[y] = line[:x] + text + line[x:]

    def overwrite (self, x, y, text):
        self.ensure_line (x, y)
        line = self.lines[y]
        self.lines[y] = line[:x] + text + line[x + len (text):]

    def insert_newline (self, x, y):
        self.ensure_line (x, y)
        line = self.lines[y]
        self.lines[y] = line[:x]
        self.lines.insert (y + 1, line[x:])

    def merge_lines (self, y):
        if y + 1 >= len (self.lines):
            return
        self.lines[y] = self.lines[y] + self.lines[y + 1]
        self.lines.pop (y + 1)

    def delete (self, x, y, count):
        if y >= len (self.lines):
            return
        line = self.lines[y]
        self.lines[y] = line[:x] + line[x + count:]

class TextView:
    def __init__ (self, buffer):
        self.buffer = buffer
        self.cursor = (0, 0)

    def anchor_cursor (self):
        self.cursor = (self.cursor[0], min (self.cursor[1], self.get_current_line_length ()))

    def insert (self, text):
        self.anchor_cursor ();
        self.buffer.insert (self.cursor[1], self.cursor[0], text)
        self.cursor = (self.cursor[0], self.cursor[1] + len (text))

    def newline (self):
        self.buffer.insert_newline (self.cursor[1], self.cursor[0])
        self.cursor = (self.cursor[0] + 1, 0)

    def backspace (self):
        if self.cursor[1] == 0:
            if self.cursor[0] > 0:
                self.cursor = (self.cursor[0] - 1, len (self.buffer.lines[self.cursor[0] - 1]))
                self.buffer.merge_lines (self.cursor[0])
        else:
            self.buffer.delete (self.cursor[1] - 1, self.cursor[0], 1)
            self.cursor = (self.cursor[0], self.cursor[1] - 1)

    def delete (self):
        self.anchor_cursor ();
        if self.cursor[1] == self.get_current_line_length ():
            self.buffer.merge_lines (self.cursor[0])
        else:
            self.buffer.delete (self.cursor[1], self.cursor[0], 1)

    def get_current_line_length (self):
        return self.buffer.get_line_length (self.cursor[0])

    def left (self):
        self.anchor_cursor ();
        self.cursor = (self.cursor[0], max (self.cursor[1] - 1, 0))

    def right (self):
        self.cursor = (self.cursor[0], min (self.cursor[1] + 1, self.get_current_line_length ()))

    def up (self):
        self.cursor = (max (self.cursor[0] - 1, 0), self.cursor[1])

    def down (self):
        self.cursor = (min (self.cursor[0] + 1, len (self.buffer.lines) - 1), self.cursor[1])

    def home (self):
        self.cursor = (self.cursor[0], 0)

    def end (self):
        self.cursor = (self.cursor[0], self.get_current_line_length ())

    def get_cursor (self):
        return (self.cursor[0], min (self.cursor[1], self.get_current_line_length ()) + 3)

    def render (self, frame):
        frame.clear ()
        for y in range (frame.height):
            frame.render_text (0, y, '%2d' % (y + 1))
        for (y, line) in enumerate (self.buffer.lines):
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
        elif key == '\n':
            self.newline ()
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
        self.buffer = TextBuffer ()

    def run (self, args):
        self.read_buffer = ''
        if self.pid != 0:
            os.kill (self.pid, signal.SIGTERM)
        (self.pid, self.fd) = pty.fork ()
        if self.pid == 0:
            subprocess.run (args)
            exit ()

    def read (self):
        try:
            self.read_buffer += os.read (self.fd, 65535).decode ('utf-8')
        except:
            os.close (self.fd)

        # Process data
        while self.read_buffer != '':
            c = self.read_buffer[0]
            #open ('debug.log', 'a').write ('Character {}\n'.format (ord (c)))
            if c == '\033':
                if len (self.read_buffer) == 1:
                    return
                # ANSI CSI
                if self.read_buffer[1] == '[':
                    # Find end characters
                    end = 2
                    def is_csi_end (c):
                        n = ord (c)
                        return n >= 0x40 and n <= 0x7F;
                    while end < len (self.read_buffer) and not is_csi_end (self.read_buffer[end]):
                        end += 1
                    if end >= len (self.read_buffer):
                        return # Not got full sequence, wait for more data

                    code = self.read_buffer[end]
                    params = self.read_buffer[2:end]
                    #open ('debug.log', 'a').write ('CSI code={} params={}\n'.format (code, params))
                    self.read_buffer = self.read_buffer[end + 1:]
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
                            self.buffer.clear ()
                        else:
                            open ('debug.log', 'a').write ('Unknown ED mode={}\n'.format (params))
                    elif code == 'K': # EL - erase line
                        mode = params
                        if mode == '' or mode == '0':
                            self.erase_line (self.cursor[1], self.get_current_line_length ())
                        elif mode == '1':
                            self.erase_line (0, self.cursor[1])
                        elif mode == '2':
                            self.erase_line (0, self.get_current_line_length ())
                        else:
                            open ('debug.log', 'a').write ('Unknown EL mode={}\n'.format (params))
                    elif code == 'P': # DCH - delete characters
                        count = 1
                        if params != '':
                            count = int (params)
                        self.erase_line (self.cursor[1], min (self.cursor[1] + count, self.get_current_line_length ()));
                    else:
                        open ('debug.log', 'a').write ('Unknown CSI code={} params={}\n'.format (code, params))
                else:
                    # FIXME
                    open ('debug.log', 'a').write ('Unknown escape code {}\n'.format (ord (c)))
                    self.read_buffer = self.read_buffer[1:]
            elif c == '\b': # BS
                self.left (1)
                self.read_buffer = self.read_buffer[1:]
            elif c == '\a': # BEL
                # FIXME: Flash bell symbol or similar?
                self.read_buffer = self.read_buffer[1:]
            elif c == '\r': # CR
                self.cursor = (self.cursor[0], 0)
                self.read_buffer = self.read_buffer[1:]
            elif c == '\n': # LF
                self.cursor = (self.cursor[0] + 1, 0)
                self.read_buffer = self.read_buffer[1:]
            elif ord (c) >= 0x20 and ord (c) <= 0x7E:
                self.insert (c)
                self.read_buffer = self.read_buffer[1:]
            elif ord (c) & 0x80 != 0: # UTF-8
                open ('debug.log', 'a').write ('FIXME: UTF-8\n')
                self.read_buffer = self.read_buffer[1:]
            else:
                open ('debug.log', 'a').write ('Unknown character {}\n'.format (ord (c)))
                self.read_buffer = self.read_buffer[1:]

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

    def get_current_line_length (self):
        return self.buffer.get_line_length (self.cursor[0])

    def erase_line (self, start, end):
        self.buffer.delete (start, self.cursor[0], end - start)

    def insert (self, text):
        self.buffer.overwrite (self.cursor[1], self.cursor[0], text)
        self.cursor = (self.cursor[0], self.cursor[1] + len (text))

    def get_cursor (self):
        return self.cursor

    def render (self, frame):
        frame.clear ()
        for (y, line) in enumerate (self.buffer.lines):
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
        self.editor = TextView (self.buffer)
        self.console = Console ()
        self.console_focus = False
        self.fullscreen = False

    def run (self):
        self.sel.register (sys.stdin, selectors.EVENT_READ)
        try:
            for line in open ('main.py').read ().split ('\n'):
                self.buffer.lines.append (line)
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

        if self.fullscreen:
            if self.console_focus:
                (cursor_y, cursor_x) = self.console.get_cursor ()
            else:
                (cursor_y, cursor_x) = self.editor.get_cursor ()
        else:
            if self.console_focus:
                (cursor_y, cursor_x) = self.console.get_cursor ()
                cursor_y += max_lines // 2 + 1
            else:
                (cursor_y, cursor_x) = self.editor.get_cursor ()
        self.screen.move (cursor_y, cursor_x)
        self.screen.refresh ()

    def run_program (self):
        f = open ('main.py', 'w')
        for line in self.buffer.lines:
            f.write (line + '\n')
        f.close ()
        if self.console.pid != 0:
            self.sel.unregister (self.console.fd)
        self.console.run (['python3', 'main.py'])
        self.sel.register (self.console.fd, selectors.EVENT_READ)

    def render (self, frame):
        editor_height = frame.height // 2
        console_height = frame.height - editor_height - 1

        if self.fullscreen:
            if self.console_focus:
                self.console.render (frame)
            else:
                self.editor.render (frame)
        else:
            editor_frame = Frame (frame.width, editor_height)
            self.editor.render (editor_frame)
            frame.composite (0, 0, editor_frame)

            frame.render_text (0, editor_height, 'Console ' + 'X' * (frame.width - 8))

            console_frame = Frame (frame.width, console_height)
            self.console.render (console_frame)
            frame.composite (0, editor_height + 1, console_frame)

    def handle_key (self, key):
        if key == 'KEY_F(4)':
            self.console_focus = not self.console_focus
        elif key == 'KEY_F(5)':
            self.run_program ()
        elif key == 'KEY_F(8)': # F11?
            self.fullscreen = not self.fullscreen
        elif self.console_focus:
            self.console.handle_key (key)
        else:
            self.editor.handle_key (key)

def main (screen):
    pride = Pride (screen)
    pride.run ()

curses.wrapper (main)
