# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .keyinputevent import Key
from .widget import Widget
from .textbuffer import get_line_width

class TextView (Widget):
    def __init__ (self, buffer):
        Widget.__init__ (self)
        self.buffer = buffer
        self.cursor = (0, 0)
        self.start_line = 0
        self.set_scale (1.0, 1.0)

    def get_size (self):
        return (1, 1)

    def get_current_line_width (self):
        if len (self.buffer.lines) == 0:
            return 0
        return get_line_width (self.buffer.lines[self.cursor[0]])

    def anchor_cursor (self):
        self.cursor = (self.cursor[0], min (self.cursor[1], self.get_current_line_width ()))

    def insert (self, text):
        self.anchor_cursor ();
        step = self.buffer.insert (self.cursor[1], self.cursor[0], text)
        self.cursor = (self.cursor[0], self.cursor[1] + step)

    def newline (self):
        self.anchor_cursor ();
        self.buffer.split_line (self.cursor[1], self.cursor[0])
        self.cursor = (self.cursor[0] + 1, 0)

    def backspace (self):
        self.anchor_cursor ();
        if self.cursor[1] == 0:
            if self.cursor[0] > 0:
                self.cursor = (self.cursor[0] - 1, len (self.buffer.lines[self.cursor[0] - 1]))
                self.buffer.merge_lines (self.cursor[0])
        else:
            step = self.buffer.delete_left (self.cursor[1], self.cursor[0])
            self.cursor = (self.cursor[0], self.cursor[1] + step)

    def delete (self):
        self.anchor_cursor ();
        if self.cursor[1] == self.get_current_line_width ():
            self.buffer.merge_lines (self.cursor[0])
        else:
            step = self.buffer.delete_right (self.cursor[1], self.cursor[0])
            self.cursor = (self.cursor[0], self.cursor[1] + step)

    def indent (self):
        step = self.buffer.insert (0, self.cursor[0], '    ')
        self.cursor = (self.cursor[0], self.cursor[1] + step)

    def unindent (self):
        if not self.buffer.lines[self.cursor[0]].startswith ('    '):
            # FIXME: Notify user of error
            return
        for i in range (4):
            step = self.buffer.delete_right (0, self.cursor[0])
            self.cursor = (self.cursor[0], self.cursor[1] + step)

    def left (self):
        self.anchor_cursor ();
        if self.cursor[1] == 0 and self.cursor[0] > 0:
            self.cursor = (self.cursor[0] - 1, get_line_width (self.buffer.lines[self.cursor[0] - 1]))
        else:
            self.cursor = (self.cursor[0], self.buffer.position_left (self.cursor[1], self.cursor[0]))

    def right (self):
        if self.cursor[1] == self.get_current_line_width () and self.cursor[0] < len (self.buffer.lines) - 1:
            self.cursor = (self.cursor[0] + 1, 0)
        else:
            self.cursor = (self.cursor[0], self.buffer.position_right (self.cursor[1], self.cursor[0]))

    def up (self):
        self.cursor = (max (self.cursor[0] - 1, 0), self.cursor[1])

    def down (self):
        self.cursor = (min (self.cursor[0] + 1, len (self.buffer.lines) - 1), self.cursor[1])

    def home (self):
        self.cursor = (self.cursor[0], 0)

    def end (self):
        self.cursor = (self.cursor[0], self.get_current_line_width ())

    def next_page (self):
        self.cursor = (len (self.buffer.lines) - 1, self.cursor[1])

    def prev_page (self):
        self.cursor = (0, self.cursor[1])

    def document_start (self):
        self.cursor = (0, 0)

    def document_end (self):
        if len (self.buffer.lines) == 0:
            self.cursor = (0, 0)
        else:
            self.cursor = (len (self.buffer.lines) - 1, get_line_width (self.buffer.lines[-1]))

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
            frame.render_text (line_number_column_width - len (line_number) - 1, y - self.start_line, line_number, "#00FFFF")
            frame.render_text (line_number_column_width, y - self.start_line, self.buffer.lines[y])

        frame.cursor = (self.cursor[0] - self.start_line, min (self.cursor[1], self.get_current_line_width ()) + self.get_line_number_column_width ())

    def handle_character_event (self, event):
        self.insert (chr (event.character))

    def handle_key_event (self, event):
        if event.key == Key.BACKSPACE:
            self.backspace ()
        elif event.key == Key.DELETE or event.key == Key.CTRL_D:
            self.delete ()
        elif event.key == Key.LEFT:
            self.left ()
        elif event.key == Key.RIGHT:
            self.right ()
        elif event.key == Key.UP:
            self.up ()
        elif event.key == Key.DOWN:
            self.down ()
        elif event.key == Key.HOME or event.key == Key.CTRL_A:
            self.home ()
        elif event.key == Key.END or event.key == Key.CTRL_E:
            self.end ()
        elif event.key == Key.PAGE_DOWN:
            self.next_page ()
        elif event.key == Key.PAGE_UP:
            self.prev_page ()
        elif event.key == Key.TAB:
            self.indent ()
        elif event.key == Key.SHIFT_TAB:
            self.unindent ()
        elif event.key == Key.ENTER:
            self.newline ()
        elif event.key == Key.CTRL_HOME:
            self.document_start ()
        elif event.key == Key.CTRL_END:
            self.document_end ()
        else:
            open ('debug.log', 'a').write ('Unhandled editor key {}\n'.format (event.key))
