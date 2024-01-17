import curses

def mywrapper(fn):

    def inner():
        try:
            if 1:  # Call our own version of curses.initscr().
                import _curses
                # This crashes on Python 3.12.
                    # setupterm(term=_os.environ.get("TERM", "unknown"),
                        # fd=_sys.__stdout__.fileno())
                stdscr = _curses.initscr()
                for key, value in _curses.__dict__.items():
                    if key[0:4] == 'ACS_' or key in ('LINES', 'COLS'):
                        setattr(curses, key, value)
            else:
                stdscr = curses.initscr()

            curses.noecho()
            curses.cbreak()
            curses.start_color()
            stdscr.keypad(True)
            stdscr.refresh()
            fn(stdscr)

        finally:
            curses.nocbreak()
            stdscr.keypad(False)
            curses.echo()
            curses.endwin()

    return inner
