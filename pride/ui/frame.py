# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

import unicodedata

class Pixel:
    def __init__ (self):
        self.set_value (' ')

    def set_value (self, character, foreground = '#FFFFFF', background = '#000000'):
        self.character = character
        self.foreground = foreground
        self.background = background

    def copy (self, pixel):
        self.character = pixel.character
        self.foreground = pixel.foreground
        self.background = pixel.background

    def is_wide (self):
        return unicodedata.east_asian_width (self.character[0]) in ('W', 'F')

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

    def clear (self, color = '#000000'):
        self.fill (0, 0, self.width, self.height, ' ', background = color)

    def fill (self, x, y, width, height, character, foreground = '#FFFFFF', background = '#000000'):
        height = min (height, self.height)
        width = min (width, self.width)
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

    def render_text (self, x, y, text, foreground = '#FFFFFF', background = '#000000'):
        if y >= self.height:
            return
        line = self.buffer[y]
        x_ = x
        for c in text:
            if x_ >= self.width:
                break
            line[x_].set_value (c, foreground, background)
            if ord (c) >= 0xFE00 and ord (c) <= 0xFE0F: # Variation selectors
                if x_ > x:
                    line[x_ - 1].character += c
            elif unicodedata.east_asian_width (c) in ('W', 'F'):
                x_ += 2
            else:
                x_ += 1

    def render_image (self, x, y, lines, color_lines = None, color_map = None):
        for (i, source_line) in enumerate (lines):
            if y + i >= self.height:
                return
            line = self.buffer[y + i]
            for (j, c) in enumerate (source_line):
                (foreground, background) = ('#FFFFFF', '#000000')
                if color_lines is not None:
                    color_code = color_lines[i][j]
                    (foreground, background) = color_map.get (color_code, ('#FFFFFF', '#000000'))
                if x + j >= self.width:
                    break
                line[x + j].set_value (c, foreground, background)

    def render_horizontal_bar (self, x, y, width, start_fraction = 8, end_fraction = 8, foreground = '#FFFFFF', background = '#000000'):
        if y >= self.height:
            return
        line = self.buffer[y]
        for i in range (width):
            if x + i >= self.width:
                break
            if i == 0 and start_fraction > 0 and start_fraction < 8:
                line [x + i].set_value (chr (0x2588 + start_fraction), background, foreground)
            elif i == width - 1 and end_fraction > 0 and end_fraction < 8:
                line [x + i].set_value (chr (0x2588 + (8 - end_fraction)), foreground, background)
            else:
                line [x + i].set_value ('█', foreground, background)

    def render_vertical_bar (self, x, y, height, start_fraction = 0, end_fraction = 0, foreground = '#FFFFFF', background = '#000000'):
        if x >= self.width:
            return
        for i in range (height):
            if y + i >= self.height:
                break
            line = self.buffer[y + i]
            if i == 0 and start_fraction > 0 and start_fraction < 8:
                line [x].set_value (chr (0x2580 + start_fraction), foreground, background)
            elif i == height - 1 and end_fraction > 0 and end_fraction < 8:
                line [x].set_value (chr (0x2580 + (8 - end_fraction)), background, foreground)
            else:
                line [x].set_value ('█', foreground, background)
