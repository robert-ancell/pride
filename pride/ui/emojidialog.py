# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

import unicodedata
import xml.etree.ElementTree as ET

from .widget import Widget
from .keyinputevent import Key

class EmojiDialog (Widget):
    def __init__ (self):
        Widget.__init__ (self)
        self.selected = (0, 0)
        self.selected_character = ''
        self.filter = ''
        self.placeholder_text = 'Search' # FIXME: Make translatable

        class Character:
            def __init__ (self, character, names):
                self.character = character
                self.names = names
        self.characters = []
        tree = ET.parse ('emoji.xml')
        root = tree.getroot ()
        for c0 in root:
            if c0.tag == 'annotations':
                for c1 in c0:
                    if c1.tag == 'annotation':
                        if c1.get ('type', '') == 'tts':
                            continue
                        cp = c1.get ('cp')
                        if len (cp) > 1:
                            continue
                        # Skip skin tones, as we don't support combining characters
                        if ord (cp) >= 0x1f3fb and ord (cp) <= 0x1f3ff:
                            continue

                        names = []
                        for name in c1.text.split ('|'):
                            names.append (name.strip ().lower ())

                        self.characters.append (Character (cp, names))

    def select_character (self, character):
        pass

    def get_size (self):
        return (max (4, len (self.placeholder_text)), 5)

    def get_characters (self, query):
        exact_matches = []
        prefix_matches = []
        matches = []
        for c in self.characters:
            def matches_exact (query, names):
                for name in names:
                    if name == query:
                        return True
                return False
            def matches_prefix (query, names):
                for name in names:
                    if name.startswith (query):
                        return True
                return False
            def matches_segment (query, names):
                for name in names:
                    if query in name:
                        return True
                return False
            if matches_exact (query, c.names):
                exact_matches.append (c.character)
            elif matches_prefix (query, c.names):
                prefix_matches.append (c.character)
            elif matches_segment (query, c.names):
                matches.append (c.character)

        return exact_matches + prefix_matches + matches

    def handle_key_event (self, event):
        if event.key == Key.ENTER:
            self.select_character (self.selected_character)
        elif event.key == Key.BACKSPACE:
            self.filter = self.filter[:-1]
            self.selected = (0, 0)
        elif event.key == Key.UP:
            self.selected = (max (self.selected[0] - 1, 0), self.selected[1])
        elif event.key == Key.DOWN:
            self.selected = (min (self.selected[0] + 1, self.n_rows - 1), self.selected[1])
        elif event.key == Key.LEFT:
            self.selected = (self.selected[0], max (self.selected[1] - 1, 0))
        elif event.key == Key.RIGHT:
            self.selected = (self.selected[0], min (self.selected[1] + 1, self.n_cols - 1))
        else:
            return False

        return True

    def handle_character_event (self, event):
        self.filter += chr (event.character)
        self.selected = (0, 0)
        return True

    def render (self, frame, theme):
        matched_characters = self.get_characters (self.filter)
        self.selected_character = ''

        self.n_rows = (frame.height - 1) // 2
        self.n_cols = (frame.width - 1) // 3

        frame.clear ()
        frame.fill (0, 0, self.n_cols * 3 + 1, self.n_rows * 2 + 2, background = theme.text_background)

        line = 1
        if self.selected == (0, 0):
            text = '┏'
        else:
            text = '╭'
        for c in range (self.n_cols):
            if c != 0:
                if self.selected == (0, c - 1):
                    text += '┱'
                elif self.selected == (0, c):
                    text += '┲'
                else:
                    text += '┬'
            if self.selected == (0, c):
                text += '━━'
            else:
                text += '──'
        if self.selected == (0, self.n_cols - 1):
            text += '┓'
        else:
            text += '╮'
        frame.render_text (0, line, text, theme.border_color)
        line += 1
        character_index = 0
        for r in range (self.n_rows):
            if self.selected == (r, 0):
                text = '┃'
            else:
                text = '│'
            for c in range (self.n_cols):
                if character_index < len (matched_characters):
                    ch = matched_characters[character_index]
                    if self.selected == (r, c):
                        self.selected_character = ch + '\uFE0F' # Variation selector 16 - Emoji form
                else:
                    ch = ' '
                character_index += 1
                text += ch + '\uFE0F' # Variation selector 16 - Emoji form
                if unicodedata.east_asian_width (ch) not in ('W', 'F'): # Defined in http://www.unicode.org/reports/tr11/#
                    text += ' '
                if self.selected == (r, c) or self.selected == (r, c + 1):
                    text += '┃'
                else:
                    text += '│'
            frame.render_text (0, line, text, theme.border_color)
            line += 1
            if r < self.n_rows - 1:
                if self.selected == (r, 0):
                    text = '┡'
                elif self.selected == (r + 1, 0):
                    text = '┢'
                else:
                    text = '├'
                for c in range (self.n_cols):
                    if c != 0:
                        if self.selected == (r, c):
                            text += '╄'
                        elif self.selected == (r + 1, c):
                            text += '╆'
                        elif self.selected == (r, c - 1):
                            text += '╃'
                        elif self.selected == (r + 1, c - 1):
                            text += '╅'
                        else:
                            text += '┼'
                    if self.selected == (r, c) or self.selected == (r + 1, c):
                        text += '━━'
                    else:
                        text += '──'
                if self.selected == (r, c):
                    text += '┩'
                elif self.selected == (r + 1, c):
                    text += '┪'
                else:
                    text += '┤'
            else:
                if self.selected == (self.n_rows - 1, 0):
                    text = '┗'
                else:
                    text = '╰'
                for c in range (self.n_cols):
                    if c != 0:
                        if self.selected == (r, c):
                            text += '┺'
                        elif self.selected == (r, c - 1):
                            text += '┹'
                        else:
                            text += '┴'
                    if self.selected == (self.n_rows - 1, c):
                        text += '━━'
                    else:
                        text += '──'
                if self.selected == (self.n_rows - 1, self.n_cols - 1):
                    text += '┛'
                else:
                    text += '╯'
            frame.render_text (0, line, text, theme.border_color)
            line += 1

        if self.filter != '':
            frame.render_text (1, 0, self.filter, theme.text_color)
        else:
            frame.render_text (1, 0, self.placeholder_text, theme.dim_text_color)
        frame.cursor = (1 + len (self.filter), 0)
