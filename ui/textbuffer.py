# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

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
