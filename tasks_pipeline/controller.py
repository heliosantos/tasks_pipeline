
from .util import InputMode
from contextlib import suppress
import curses
import asyncio


async def process_input(stdscr, control, cancel_all_tasks, start_tasks):
    stdscr.nodelay(True)

    control['mode'] = InputMode.NONE
    control['selectedTask'] = ''
    control['command'] = ''

    while True:
        with suppress(curses.error):
            k = stdscr.getkey()
            match control['mode']:
                case InputMode.NONE:
                    if k == ':':
                        control['mode'] = InputMode.GET_TASK
                        control['selectedTask'] = ''
                    if k.lower() == 'c':
                        await cancel_all_tasks()
                    if k.lower() == 's':
                        asyncio.create_task(start_tasks())
                    if k.lower() == 'x':
                        return

                case InputMode.GET_TASK:
                    if k == '\n':
                        control['mode'] = InputMode.GET_COMMAND
                    else:
                        control['selectedTask'] += k

                case InputMode.GET_COMMAND:
                    if k == '\n':
                        control['mode'] = InputMode.NONE
                    else:
                        control['command'] += k
            control['hasUpdates'] = True
        await asyncio.sleep(0.1)
