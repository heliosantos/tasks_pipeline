
from contextlib import suppress
import curses
import asyncio
import logging

from .tasks import TaskStatus
from .task_model import TaskModel, InputMode


logger = logging.getLogger('tasks_pipeline.run_process_task')


async def disable_task(task):
    task['instance'].status = TaskStatus.DISABLED


async def enable_task(task):
    task['instance'].status = TaskStatus.NOT_STARTED


async def execute_command(model):
    logger.info(f'run command: {model.selectedTask["index"]=}, {model.commandText=}')
    match model.commandText.lower():
        case 'disable':
            await disable_task(model.selectedTask)
    match model.commandText.lower():
        case 'enable':
            await enable_task(model.selectedTask)


async def process_input(stdscr, model: TaskModel, cancel_all_tasks, start_tasks):
    stdscr.nodelay(True)

    model.inputMode = InputMode.NONE
    model.selectedTaskText = ''
    model.commandText = ''

    while True:
        with suppress(curses.error):
            k = stdscr.getkey()
            match model.inputMode:
                case InputMode.NONE:
                    if k == ':':
                        model.inputMode = InputMode.GET_TASK
                        model.selectedTaskText = ''
                        model.commandText = ''
                    if k.lower() == 's':
                        asyncio.create_task(start_tasks())
                    if k.lower() == 'x':
                        return

                case InputMode.GET_TASK:
                    if k == '\n':
                        model.selectTask(model.selectedTaskText)
                        if model.selectedTask:
                            model.inputMode = InputMode.GET_COMMAND
                        else:
                            model.inputMode = InputMode.NONE
                    else:
                        model.selectedTaskText += k

                case InputMode.GET_COMMAND:
                    if k.lower() == 'd':
                        model.commandText = 'disable'
                        await execute_command(model)
                        model.selectedTaskText = ''
                        model.commandText = ''
                        model.inputMode = InputMode.NONE
                    if k.lower() == 'e':
                        model.commandText = 'enable'
                        await execute_command(model)
                        model.selectedTaskText = ''
                        model.commandText = ''
                        model.inputMode = InputMode.NONE

            model.hasUpdates = True
        await asyncio.sleep(0.1)
