# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

import os
import pty
import selectors
import signal
import subprocess

from .keyinputevent import Key
from .textbuffer import TextBuffer
from .widget import Widget

class Console (Widget):
    def __init__ (self, selector):
        Widget.__init__ (self)
        self.selector = selector
        self.pid = 0
        self.fd = -1
        self.cursor = (0, 0)
        self.buffer = TextBuffer ()

    def handle_selector_event (self, key, mask):
        if key.fd == self.fd:
            if not self.read ():
                pass
            # FIXME
            #self.selector.unregister (self.fd)
            #self.console.run (['python3', '-q'])
            #self.selector.register (self.fd, selectors.EVENT_READ)

    def run (self, args):
        if self.pid != 0:
            self.selector.unregister (self.fd)

        self.read_buffer = ''
        last_line = 0
        for (i, line) in enumerate (self.buffer.lines):
            if line != '':
                last_line = i
        self.cursor = (last_line, 0)
        if self.pid != 0:
            os.kill (self.pid, signal.SIGTERM)
        (self.pid, self.fd) = pty.fork ()
        if self.pid == 0:
            subprocess.run (args)
            exit ()
        self.selector.register (self.fd, selectors.EVENT_READ)

    def read (self):
        try:
            self.read_buffer += os.read (self.fd, 65535).decode ('utf-8') # FIXME: Use bytes
        except:
            os.close (self.fd) # FIXME: Should unregister fd
            return False

        # Process data
        while self.read_buffer != '':
            c = self.read_buffer[0]
            #open ('debug.log', 'a').write ('Character {}\n'.format (ord (c)))
            if c == '\033':
                if len (self.read_buffer) == 1:
                    return True
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
                        return True # Not got full sequence, wait for more data

                    code = self.read_buffer[end]
                    params = self.read_buffer[2:end]
                    #open ('debug.log', 'a').write ('console CSI code={} params={}\n'.format (code, params))
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
                            self.buffer.delete (self.cursor[1], self.cursor[0], 9999) # FIXME: End of line...
                        elif mode == '1':
                            self.buffer.delete (0, self.cursor[0], self.cursor[1])
                        elif mode == '2':
                            self.buffer.delete (0, self.cursor[0], 9999) # FIXME: End of line...
                        else:
                            open ('debug.log', 'a').write ('Unknown EL mode={}\n'.format (params))
                    elif code == 'P': # DCH - delete characters
                        count = 1
                        if params != '':
                            count = int (params)
                        self.buffer.delete (self.cursor[1], self.cursor[0], count)
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
                self.buffer.overwrite (self.cursor[1], self.cursor[0], c)
                self.cursor = (self.cursor[0], self.cursor[1] + 1)
                self.read_buffer = self.read_buffer[1:]
            elif ord (c) & 0x80 != 0: # UTF-8
                open ('debug.log', 'a').write ('FIXME: UTF-8\n')
                self.read_buffer = self.read_buffer[1:]
            else:
                open ('debug.log', 'a').write ('Unknown character {}\n'.format (ord (c)))
                self.read_buffer = self.read_buffer[1:]

        return True

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

    def render (self, frame):
        frame.clear ()
        for (y, line) in enumerate (self.buffer.lines):
            frame.render_text (0, y, line)
        frame.cursor = self.cursor

    def handle_character_event (self, event):
        os.write (self.fd, bytes (chr (event.character), 'utf-8'))

    def handle_key_event (self, event):
        if event.key == Key.ENTER:
            os.write (self.fd, '\n'.encode ('ascii'))
        elif event.key == Key.TAB:
            os.write (self.fd, '\t'.encode ('ascii'))
        elif event.key == Key.BACKSPACE:
            os.write (self.fd, '\b'.encode ('ascii'))
        elif event.key == Key.DELETE:
            os.write (self.fd, '\033[3~'.encode ('ascii'))
        elif event.key == Key.UP:
            os.write (self.fd, '\033[A'.encode ('ascii'))
        elif event.key == Key.DOWN:
            os.write (self.fd, '\033[B'.encode ('ascii'))
        elif event.key == Key.RIGHT:
            os.write (self.fd, '\033[C'.encode ('ascii'))
        elif event.key == Key.LEFT:
            os.write (self.fd, '\033[D'.encode ('ascii'))
        elif event.key == Key.HOME:
            os.write (self.fd, '\033[H'.encode ('ascii'))
        elif event.key == Key.END:
            os.write (self.fd, '\033[F'.encode ('ascii'))