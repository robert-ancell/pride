# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

import unicodedata

def get_variation_selector (c):
    if ord (c) >= 0xFE00 and ord (c) <= 0xFE0F:
        return ord (c) - 0xFE00 + 1
    else:
        return 0

def get_char_width (c):
    if len (c) == 2 and get_variation_selector (c[1]) == 16: # Emoji
        return 2
    elif unicodedata.east_asian_width (c) in ('W', 'F'):
        return 2
    else:
        return 1

class unicode_iterator:
    def __init__ (self, string):
        self.string = string
        self.index = 0

    def __iter__ (self):
        return self

    def __next__ (self):
        if self.index >= len (self.string):
            raise StopIteration

        c = self.string[self.index]

        # Keep variation selectors and combining diacritics
        if self.index + 1 < len (self.string):
            c2 = self.string[self.index + 1]
            if get_variation_selector (c2) != 0 or unicodedata.combining (c2) != 0:
                c += c2
                self.index += 1

        self.index += 1
        return c

def get_line_width (line):
    length = 0
    for c in unicode_iterator (line):
        length += get_char_width (c)
    return length

def _explode_line (line, width = 0):
    exploded = []
    for c in unicode_iterator (line):
        exploded.append (c)
        if get_char_width (c) == 2:
            exploded.append (None)
    while len (exploded) < width:
        exploded.append (' ')
    return exploded

def _implode_line (line):
    imploded = ''
    for c in line:
        if c != None:
            imploded += c
    return imploded

class TextBuffer:
    def __init__ (self, changed_callback = None):
        self.changed_callback = changed_callback
        self.lines = []

    def clear (self):
        self.lines = []

    def position_left (self, x, y):
        if y >= len (self.lines):
            return x
        if x <= 0:
            return 0
        last_position = 0
        p = 0
        for c in unicode_iterator (self.lines[y]):
            p += get_char_width (c)
            if p >= x:
                break
            last_position = p
        return last_position

    def position_right (self, x, y):
        if y >= len (self.lines):
            return x
        if x >= get_line_width (self.lines[y]):
            return x
        last_position = 0
        p = 0
        for c in unicode_iterator (self.lines[y]):
            p += get_char_width (c)
            if last_position >= x:
                break
            last_position = p
        return p

    # Ensure lines exists to requested position
    def _ensure_line (self, y):
        while len (self.lines) <= y:
            self.lines.append ('')

    def _update_line (self, y, line):
        if self.lines[y] == line:
            return
        self.lines[y] = line
        if self.changed_callback is not None:
            self.changed_callback ()

    def insert (self, x, y, text, append_double_width = True):
        self._ensure_line (y)
        exploded = _explode_line (self.lines[y], x)
        step = get_line_width (text)
        # If inside a double width, move to next position or replace double with a space
        if x < len (exploded) and exploded[x] == None:
            if append_double_width:
                step += 1
                exploded.insert (x + 1, text)
            else:
                exploded.pop (x - 1)
                exploded.insert (x, ' ')
                exploded.insert (x + 1, text)
        else:
            exploded.insert (x, text)
        self._update_line (y, _implode_line (exploded))
        return step

    def overwrite (self, x, y, text):
        exploded_text = _explode_line (text)
        self._ensure_line (y)
        exploded = _explode_line (self.lines[y], x + len (exploded_text))
        # If start inside double width insert space
        if x < len (exploded) and exploded[x] == None:
            exploded = exploded[:x - 1] + ' ' + exploded_text + exploded[x + len (exploded_text):]
        else:
            exploded = exploded[:x] + exploded_text + exploded[x + get_line_width (exploded_text):]
        self._update_line (y, _implode_line (exploded))

    def split_line (self, x, y):
        self._ensure_line (y)
        exploded = _explode_line (self.lines[y], x)
        self._update_line (y, _implode_line (exploded[:x]))
        self.lines.insert (y + 1, _implode_line (exploded[x:]))

    def merge_lines (self, y):
        if y + 1 >= len (self.lines):
            return
        self._update_line (y, self.lines[y] + self.lines[y + 1])
        self.lines.pop (y + 1)

    def delete_left (self, x, y):
        if x == 0:
            return 0
        self._ensure_line (y)
        exploded = _explode_line (self.lines[y], x)
        # If deleting a double width character then delete two spaces
        if exploded[x - 1] == None:
            exploded.pop (x - 2)
            step = -2
        else:
            exploded.pop (x - 1)
            step = -1
        self._update_line (y, _implode_line (exploded))
        return step

    def delete_right (self, x, y):
        self._ensure_line (y)
        exploded = _explode_line (self.lines[y], x)
        # If inside double width delete that character
        if x < len (exploded) and exploded[x] == None:
            exploded.pop (x - 1)
        else:
            exploded.pop (x)
        self._update_line (y, _implode_line (exploded))
        return 0

if __name__ == '__main__':
    b = TextBuffer ()
    assert (b.lines == [])

    # Insert line
    b.insert (0, 0, 'Hello world')
    assert (b.lines == ['Hello world'])

    # Clears
    b.clear ()
    assert (b.lines == [])

    # First character
    b.insert (0, 0, 'B')
    assert (b.lines == ['B'])

    # Prepend
    b.insert (0, 0, 'A')
    assert (b.lines == ['AB'])

    # Append
    b.insert (2, 0, 'D')
    assert (b.lines == ['ABD'])

    # Insert
    b.insert (2, 0, 'C')
    assert (b.lines == ['ABCD'])

    # Delete middle (left)
    b.delete_left (3, 0)
    assert (b.lines == ['ABD'])

    # Delete middle (right)
    b.delete_right (1, 0)
    assert (b.lines == ['AD'])

    # Delete end
    b.delete_left (2, 0)
    assert (b.lines == ['A'])

    # Delete start
    b.delete_right (0, 0)
    assert (b.lines == [''])

    # Overwrite (middle)
    b.insert (0, 0, '1234')
    b.overwrite (1, 0, 'AB')
    assert (b.lines == ['1AB4'])

    # Overwrite (start)
    b.overwrite (0, 0, 'WX')
    assert (b.lines == ['WXB4'])

    # Overwrite (end)
    b.overwrite (2, 0, 'YZ')
    assert (b.lines == ['WXYZ'])

    # Overwrite (append)
    b.overwrite (3, 0, 'AB')
    assert (b.lines == ['WXYAB'])

    # Overwrite (append with space)
    b.overwrite (6, 0, '123')
    assert (b.lines == ['WXYAB 123'])

    # Split line
    b.clear ()
    b.insert (0, 0, '1234')
    b.split_line (2, 0)
    assert (b.lines == ['12', '34'])

    # Merge lines
    b.merge_lines (0)
    assert (b.lines == ['1234'])
