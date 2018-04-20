#!/usr/bin/python3

# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

# ＰｒＩＤＥ

import sys
import os
import curses
import selectors
import pty
import subprocess
import signal

class Widget:
    def __init__ (self):
        self.visible = True

    def get_size (self):
        return (0, 0)

    def handle_event (self, event):
        if isinstance (event, CharacterInputEvent):
            self.handle_character_event (event)
        elif isinstance (event, KeyInputEvent):
            self.handle_key_event (event)

    def handle_character_event (self, event):
        pass

    def handle_key_event (self, event):
        pass

    def render (self, frame):
        pass

class Pixel:
    def __init__ (self):
        self.set_value (ord (' '))

    def set_value (self, character, foreground = curses.COLOR_WHITE, background = curses.COLOR_BLACK):
        self.character = character
        self.foreground = foreground
        self.background = background

    def copy (self, pixel):
        self.character = pixel.character
        self.foreground = pixel.foreground
        self.background = pixel.background

class InputEvent:
    def __init__ (self):
        pass

class CharacterInputEvent (InputEvent):
    def __init__ (self, character):
        self.character = character

    def __str__ (self):
        return 'CharacterInputEvent({})'.format (self.character)

class KeyInputEvent (InputEvent):
    def __init__ (self, key):
        self.key = key

    def __str__ (self):
        return 'KeyInputEvent({})'.format (self.key)

class CursorInputEvent (InputEvent):
    def __init__ (self, line_step, row_step, relative = True):
        self.line_step = line_step
        self.row_step = row_step
        self.relative = relative

    def __str__ (self):
        return 'CursorInputEvent(line_step = {}, row_step = {}, relative = {})'.format (self.line_step, self.row_step, self.relative)

class Frame:
    def __init__ (self, width, height):
        self.width = width
        self.height = height
        self.buffer = []
        for y in range (height):
            line = []
            for x in range (width):
                line.append (Pixel ())
            self.buffer.append (line)
        self.cursor = (0, 0)

    def clear (self):
        self.fill (0, 0, self.width, self.height, ord (' '))

    def fill (self, x, y, width, height, character, foreground = curses.COLOR_WHITE, background = curses.COLOR_BLACK):
        for y_ in range (y, height):
            for x_ in range (x, width):
                self.buffer[y_][x_].set_value (character, foreground, background)

    def composite (self, x, y, frame):
        # FIXME: Make SubFrame that re-uses buffer?
        width = min (self.width - x, frame.width)
        height = min (self.height - y, frame.height)
        for y_ in range (height):
            source_line = frame.buffer[y_]
            target_line = self.buffer[y + y_]
            for x_ in range (width):
                target_line[x + x_].copy (source_line[x_])

    def render_text (self, x, y, text, foreground = curses.COLOR_WHITE, background = curses.COLOR_BLACK):
        if y >= self.height:
            return
        line = self.buffer[y]
        for (i, c) in enumerate (text):
            if x + i >= self.width:
                return
            line[x + i].set_value (ord (c), foreground, background)

class List (Widget):
    def __init__ (self):
        Widget.__init__ (self)
        self.focus_child = None
        self.children = []

    def insert (self, child, index):
        self.children = self.children[:index] + [child] + self.children[index:]

    def append (self, child):
        self.insert (child, len (self.children))

    def focus (self, child):
        self.focus_child = child

    def handle_event (self, event):
        if self.focus_child is None:
            return
        self.focus_child.handle_event (event)

    def render (self, frame):
        visible_children = []
        for child in self.children:
            if child.visible:
                visible_children.append (child)

        # Allocate space for children
        n_unallocated = 0
        n_remaining = frame.height
        child_heights = {}
        for child in visible_children:
            size = child.get_size ()
            if size[0] == 0:
                n_unallocated += 1
            child_heights[child] = size[0]
            n_remaining -= size[0]

        # Divide remaining space between children
        if n_unallocated != 0 and n_remaining > 0:
            # FIXME: Use per widget weighting 0.0 - 1.0
            height_per_child = n_remaining // n_unallocated
            extra = n_remaining - height_per_child * n_unallocated
            for child in visible_children:
                if child_heights[child] == 0:
                    child_heights[child] = height_per_child
                    if extra > 0:
                        child_heights[child] += 1
                        extra -= 1

        line_offset = 0
        for child in visible_children:
            height = child_heights[child]
            child_frame = Frame (frame.width, height)
            child.render (child_frame)
            frame.composite (0, line_offset, child_frame)
            if child is self.focus_child:
                frame.cursor = (line_offset + child_frame.cursor[0], child_frame.cursor[1])
            line_offset += height

class Bar (Widget):
    def __init__ (self, title = ''):
        Widget.__init__ (self)
        self.title = title

    def set_title (self, text):
        self.title = title

    def get_size (self):
        return (1, 0)

    def render (self, frame):
        text = ''
        if self.title != '':
            text = self.title
        while len (text) < frame.width:
            text += ' '
        frame.render_text (0, 0, text, background = curses.COLOR_BLUE)

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

class TextView (Widget):
    def __init__ (self, buffer):
        Widget.__init__ (self)
        self.buffer = buffer
        self.cursor = (0, 0)
        self.start_line = 0

    def get_current_line_length (self):
        return self.buffer.get_line_length (self.cursor[0])

    def anchor_cursor (self):
        self.cursor = (self.cursor[0], min (self.cursor[1], self.get_current_line_length ()))

    def insert (self, text):
        self.anchor_cursor ();
        self.buffer.insert (self.cursor[1], self.cursor[0], text)
        self.cursor = (self.cursor[0], self.cursor[1] + len (text))

    def newline (self):
        self.anchor_cursor ();
        self.buffer.insert_newline (self.cursor[1], self.cursor[0])
        self.cursor = (self.cursor[0] + 1, 0)

    def backspace (self):
        self.anchor_cursor ();
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

    def next_page (self):
        self.cursor = (len (self.buffer.lines) - 1, self.cursor[1])

    def prev_page (self):
        self.cursor = (0, self.cursor[1])

    def get_line_number_column_width (self):
        return len ('%d' % len (self.buffer.lines)) + 1

    def render (self, frame):
        # Scroll display to show cursor
        while self.cursor[0] - self.start_line < 0:
            self.start_line -= 1
        while self.cursor[0] - self.start_line >= frame.height:
            self.start_line += 1

        frame.clear ()
        line_number_column_width = self.get_line_number_column_width ()
        for y in range (self.start_line, min (len (self.buffer.lines), frame.height + self.start_line)):
            line_number = '%d' % (y + 1)
            frame.render_text (line_number_column_width - len (line_number) - 1, y - self.start_line, line_number, curses.COLOR_CYAN)
            frame.render_text (line_number_column_width, y - self.start_line, self.buffer.lines[y])

        frame.cursor = (self.cursor[0] - self.start_line, min (self.cursor[1], self.get_current_line_length ()) + self.get_line_number_column_width ())

    def handle_character_event (self, event):
        self.insert (chr (event.character))

    def handle_key_event (self, event):
        if event.key == curses.KEY_BACKSPACE:
            self.backspace ()
        elif event.key == curses.KEY_DC:
            self.delete ()
        elif event.key == curses.KEY_LEFT:
            self.left ()
        elif event.key == curses.KEY_RIGHT:
            self.right ()
        elif event.key == curses.KEY_UP:
            self.up ()
        elif event.key == curses.KEY_DOWN:
            self.down ()
        elif event.key == curses.KEY_HOME:
            self.home ()
        elif event.key == curses.KEY_END:
            self.end ()
        elif event.key == curses.KEY_NPAGE:
            self.next_page ()
        elif event.key == curses.KEY_PPAGE:
            self.prev_page ()
        elif event.key == '\t':
            self.insert ('    ')
        elif event.key == '\n':
            self.newline ()
        else:
            open ('debug.log', 'a').write ('Unhandled editor key {}\n'.format (repr (key)))

class Console (Widget):
    def __init__ (self):
        Widget.__init__ (self)
        self.pid = 0
        self.cursor = (0, 0)
        self.buffer = TextBuffer ()

    def run (self, args):
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
        if event.key == curses.KEY_BACKSPACE:
            os.write (self.fd, '\b'.encode ('ascii'))
        elif event.key == curses.KEY_DC:
            os.write (self.fd, '\033[3~'.encode ('ascii'))
        elif event.key == curses.KEY_UP:
            os.write (self.fd, '\033[A'.encode ('ascii'))
        elif event.key == curses.KEY_DOWN:
            os.write (self.fd, '\033[B'.encode ('ascii'))
        elif event.key == curses.KEY_RIGHT:
            os.write (self.fd, '\033[C'.encode ('ascii'))
        elif event.key == curses.KEY_LEFT:
            os.write (self.fd, '\033[D'.encode ('ascii'))
        elif event.key == curses.KEY_HOME:
            os.write (self.fd, '\033[H'.encode ('ascii'))
        elif event.key == curses.KEY_END:
            os.write (self.fd, '\033[F'.encode ('ascii'))

class Pride:
    def __init__ (self, screen):
        self.screen = screen
        self.sel = selectors.DefaultSelector ()
        self.fullscreen = False

        self.main_list = List ()

        self.editor_bar = Bar ('Editor)')
        self.buffer = TextBuffer ()
        self.editor = TextView (self.buffer)
        self.main_list.append (self.editor_bar)
        self.main_list.append (self.editor)

        self.console_bar = Bar ('Console)')
        self.console = Console ()
        self.main_list.append (self.console_bar)
        self.main_list.append (self.console)

        self.main_list.focus (self.editor)

    def run (self):
        try:
            for line in open ('main.py').read ().split ('\n'):
                self.buffer.lines.append (line)
        except:
            pass
        self.console.run (['python3', '-q'])
        self.sel.register (self.console.fd, selectors.EVENT_READ)

        self.refresh ()
        self.sel.register (sys.stdin, selectors.EVENT_READ)
        while True:
            events = self.sel.select ()
            for key, mask in events:
                if key.fileobj == sys.stdin:
                    self.handle_input ()
                elif key.fd == self.console.fd:
                    if not self.console.read ():
                        pass
                        # FIXME
                        #self.sel.unregister (self.console.fd)
                        #self.console.run (['python3', '-q'])
                        #self.sel.register (self.console.fd, selectors.EVENT_READ)
            self.refresh ()

    def refresh (self):
        (max_lines, max_width) = self.screen.getmaxyx ()
        frame = Frame (max_width, max_lines)
        self.main_list.render (frame)
        color_index = 0
        for y in range (frame.height):
            text = ''
            current_color = (None, None)
            for x in range (frame.width):
                pixel = frame.buffer[y][x]
                # FIXME: Can't place in bottom right for some reason
                if y == frame.height - 1 and x == frame.width - 1:
                    break
                if (pixel.foreground, pixel.background) != current_color:
                    color_index += 1 # FIXME: Lookup table for existing colors
                    curses.init_pair (color_index, pixel.foreground, pixel.background)
                    current_color = (pixel.foreground, pixel.background)
                self.screen.addstr (y, x, chr (pixel.character), curses.color_pair (color_index))

        (cursor_y, cursor_x) = frame.cursor
        self.screen.move (cursor_y, cursor_x)
        self.screen.refresh ()

    def run_program (self):
        f = open ('main.py', 'w')
        f.write ('\n'.join (self.buffer.lines))
        f.close ()
        if self.console.pid != 0:
            self.sel.unregister (self.console.fd)
        self.console.run (['python3', 'main.py'])
        self.sel.register (self.console.fd, selectors.EVENT_READ)

    def handle_input (self):
        key = self.screen.getch ()
        if key <= 0x7F:
            self.handle_event (CharacterInputEvent (key))
        elif key > 0xFF:
            self.handle_event (KeyInputEvent (key))
        else:
            open ('debug.log', 'a').write ('Unknown input {}\n'.format (repr (key)))

    def handle_event (self, event):
        open ('debug.log', 'a').write ('EVENT {}\n'.format (event))
        if isinstance (event, KeyInputEvent):
            if event.key == curses.KEY_F4:
                if self.main_list.focus_child == self.editor:
                    self.main_list.focus (self.console)
                else:
                    self.main_list.focus (self.editor)
                self.update_visibility ()
                return
            elif event.key == curses.KEY_F5:
                self.run_program ()
                return
            elif event.key == curses.KEY_F8: # F11?
                self.fullscreen = not self.fullscreen
                self.update_visibility ()
                return

        self.main_list.handle_event (event)

    def update_visibility (self):
        focus_child = self.main_list.focus_child
        self.editor_bar.visible = not self.fullscreen or focus_child is self.editor
        self.editor.visible = not self.fullscreen or focus_child is self.editor
        self.console_bar.visible = not self.fullscreen or focus_child is self.console
        self.console.visible = not self.fullscreen or focus_child is self.console

def main (screen):
    curses.start_color ()
    curses.use_default_colors ()
    pride = Pride (screen)
    pride.run ()

curses.wrapper (main)
