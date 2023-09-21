
from contextlib import suppress
import curses
import asyncio

from .task_model import TaskModel, InputMode


async def process_input(stdscr, model: TaskModel, cancel_all_tasks, start_tasks):
    stdscr.nodelay(True)

    model.inputMode = InputMode.NONE
    model.selectedTask = ''
    model.command = ''

    while True:
        with suppress(curses.error):
            k = stdscr.getkey()
            match model.inputMode:
                case InputMode.NONE:
                    if k == ':':
                        model.inputMode = InputMode.GET_TASK
                        model.selectedTask = ''
                    if k.lower() == 'c':
                        await cancel_all_tasks()
                    if k.lower() == 's':
                        asyncio.create_task(start_tasks())
                    if k.lower() == 'x':
                        return

                case InputMode.GET_TASK:
                    if k == '\n':
                        model.inputMode = InputMode.GET_COMMAND
                    else:
                        model.selectedTask += k

                case InputMode.GET_COMMAND:
                    if k == '\n':
                        model.inputMode = InputMode.NONE
                    else:
                        model.command += k
            model.hasUpdates = True
        await asyncio.sleep(0.1)
