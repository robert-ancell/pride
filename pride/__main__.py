"""Copyright (C) 2018 Robert Ancell

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version. See http://www.gnu.org/copyleft/gpl.html the full text of the
license."""

def run ():
    import curses

    from pride.app import Pride

    def main (screen):
        curses.start_color ()
        curses.use_default_colors ()
        pride = Pride (screen)
        pride.run ()

    curses.wrapper (main)

run ()
