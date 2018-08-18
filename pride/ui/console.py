# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

import asyncio
import os
import pty
import signal
import subprocess

from .keyinputevent import Key
from .textbuffer import TextBuffer
from .widget import Widget

class Console (Widget):
    def __init__ (self, changed_callback = None):
        Widget.__init__ (self)
        self.pid = 0
        self.fd = -1
        self.cursor = (0, 0)
        self.buffer = TextBuffer (changed_callback = changed_callback)
        self.set_scale (1.0, 1.0)

    def get_size (self):
        return (0, 1)

    def handle_input (self):
        if not self.read ():
            pass
        # FIXME
        #asyncio.get_event_loop ().remove_reader (self.fd)
        #self.console.run (['python3', '-q'])
        #asyncio.get_event_loop ().add_reader (self.fd, self.handle_input)

    def run (self, args):
        if self.pid != 0:
            asyncio.get_event_loop ().remove_reader (self.fd)

        self.read_buffer = bytes ()
        last_line = 0
        for (i, line) in enumerate (self.buffer.lines):
            if line != '':
                last_line = i
        self.cursor = (0, last_line)
        if self.pid != 0:
            os.kill (self.pid, signal.SIGTERM)
        (self.pid, self.fd) = pty.fork ()
        if self.pid == 0:
            subprocess.run (args)
            exit ()
        asyncio.get_event_loop ().add_reader (self.fd, self.handle_input)

    def read (self):
        try:
            self.read_buffer += os.read (self.fd, 65535)
        except:
            os.close (self.fd) # FIXME: Should unregister fd
            return False

        #open ('debug.log', 'a').write ('processing {}\n'.format (repr (self.read_buffer)))

        # Process data
        while len (self.read_buffer) > 0:
            c = self.read_buffer[0]
            #open ('debug.log', 'a').write ('Character {}\n'.format (c))
            def is_utf8_continuation (c):
                return c & 0xC0 == 0x80
            if c == 0x1B: # ESC
                if len (self.read_buffer) == 1:
                    return True
                # ANSI CSI
                if self.read_buffer[1] == ord ('['):
                    # Find end characters
                    end = 2
                    def is_csi_end (c):
                        return c >= 0x40 and c <= 0x7F;
                    while end < len (self.read_buffer) and not is_csi_end (self.read_buffer[end]):
                        end += 1
                    if end >= len (self.read_buffer):
                        return True # Not got full sequence, wait for more data

                    code = chr (self.read_buffer[end])
                    params = self.read_buffer[2:end].decode ('ascii')
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
                        self.cursor = (col - 1, line - 1)
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
                        if mode == '' or mode == '0': # Delete cursor to end of line
                            self.buffer.overwrite (self.cursor[0], self.cursor[1], ' ' * (80 - self.cursor[0])) # FIXME: end of line...
                        elif mode == '1': # Delete from cursor to beginning of line
                            self.buffer.overwrite (0, self.cursor[1], ' ' * self.cursor[0])
                        elif mode == '2': # Clear entire line
                            self.buffer.overwrite (0, self.cursor[1], ' ' * 80) # FIXME: end of line...
                        else:
                            open ('debug.log', 'a').write ('Unknown EL mode={}\n'.format (params))
                    elif code == 'P': # DCH - delete characters
                        count = 1
                        if params != '':
                            count = int (params)
                        for i in range (count):
                            self.buffer.delete_right (self.cursor[0], self.cursor[1])
                    #elif code == 'X': # ECH - erase characters
                    else:
                        open ('debug.log', 'a').write ('Unknown CSI code={} params={}\n'.format (code, params))
                # ANSI OSC (Operating System Command)
                elif self.read_buffer[1] == ord (']'):
                    end = 2
                    def is_osc_end (c):
                        return c <= 0x1F
                    while end < len (self.read_buffer) and not is_osc_end (self.read_buffer[end]):
                        end += 1
                    if end >= len (self.read_buffer):
                        return True # Not got full sequence, wait for more data

                    code = chr (self.read_buffer[end])
                    #open ('debug.log', 'a').write ('console OSC code={}\n'.format (code))
                    self.read_buffer = self.read_buffer[end + 1:]

                    open ('debug.log', 'a').write ('Unknown OSC code={}\n'.format (code))
                else:
                    # FIXME
                    open ('debug.log', 'a').write ('Unknown escape code {}\n'.format (self.read_buffer[1]))
                    self.read_buffer = self.read_buffer[1:]
            elif c == 0x07: # BEL
                # FIXME: Flash bell symbol or similar?
                self.read_buffer = self.read_buffer[1:]
            elif c == 0x08: # BS
                self.left (1)
                self.read_buffer = self.read_buffer[1:]
            elif c == 0x0A: # LF
                self.cursor = (0, self.cursor[1] + 1)
                self.read_buffer = self.read_buffer[1:]
            elif c == 0x0D: # CR
                self.cursor = (0, self.cursor[1])
                self.read_buffer = self.read_buffer[1:]
            elif c >= 0x20 and c <= 0x7E: # UTF-8 one byte / ASCII
                self.insert (c)
                self.read_buffer = self.read_buffer[1:]
            elif c & 0xE0 == 0xC0: # UTF-8 two byte
                if len (self.read_buffer) < 2:
                    return True
                if not is_utf8_continuation (self.read_buffer[1]):
                    open ('debug.log', 'a').write ('Invalid UTF-8 sequence {}\n'.format (c))
                    self.read_buffer = self.read_buffer[1:]
                    return True
                character = (c & 0x1F) << 6 | self.read_buffer[1] & 0x3F
                self.insert (character)
                self.read_buffer = self.read_buffer[2:]
            elif c & 0xF0 == 0xE0: # UTF-8 three byte
                if len (self.read_buffer) < 3:
                    return True
                if not (is_utf8_continuation (self.read_buffer[1]) and is_utf8_continuation (self.read_buffer[2])):
                    open ('debug.log', 'a').write ('Invalid UTF-8 sequence {}\n'.format (c))
                    self.read_buffer = self.read_buffer[1:]
                    return True
                character = (c & 0x0F) << 12 | (self.read_buffer[1] & 0x3F) << 6 | self.read_buffer[2] & 0x3F
                self.insert (character)
                self.read_buffer = self.read_buffer[3:]
            elif c & 0xF8 == 0xF0: # UTF-8 four byte
                if len (self.read_buffer) < 4:
                    return True
                if not (is_utf8_continuation (self.read_buffer[1]) and is_utf8_continuation (self.read_buffer[2]) and is_utf8_continuation (self.read_buffer[3])):
                    open ('debug.log', 'a').write ('Invalid UTF-8 sequence {}\n'.format (c))
                    self.read_buffer = self.read_buffer[1:]
                    return True
                character = (c & 0x07) << 18 | (self.read_buffer[1] & 0x3F) << 12 | (self.read_buffer[2] & 0x3F) << 6 | self.read_buffer[3] & 0x3F
                self.insert (character)
                self.read_buffer = self.read_buffer[4:]
            else:
                open ('debug.log', 'a').write ('Unknown character {}\n'.format (c))
                self.read_buffer = self.read_buffer[1:]

        return True

    def insert (self, c):
        self.buffer.overwrite (self.cursor[0], self.cursor[1], chr (c))
        self.cursor = (self.cursor[0] + 1, self.cursor[1])

    def left (self, count):
        count = min (count, self.cursor[0])
        self.cursor = (self.cursor[0] - count, self.cursor[1])

    def right (self, count):
        #FIXME: count = min (count, width - cursor[0])
        self.cursor = (self.cursor[0] + count, self.cursor[1])

    def up (self, count):
        count = min (count, self.cursor[1])
        self.cursor = (self.cursor[0], self.cursor[1] - count)

    def down (self, count):
        #FIXME: count = min (count, height - cursor[1])
        self.cursor = (self.cursor[0], self.cursor[1] + count)

    def render (self, frame, theme):
        frame.clear (theme.console_background)
        for (y, line) in enumerate (self.buffer.lines):
            frame.render_text (0, y, line, theme.text_color)
        frame.cursor = self.cursor

    def handle_character_event (self, event):
        os.write (self.fd, bytes (chr (event.character), 'utf-8'))
        return True

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
        else:
            return False

        return True
