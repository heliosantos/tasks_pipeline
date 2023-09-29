from contextlib import suppress
import curses
import asyncio
import logging

from .tasks import TaskStatus
from .tasks_model import TasksModel, InputMode
from .util import tasks_apply
from .view import notify


logger = logging.getLogger("tasks_pipeline.controller")


async def start_tasks(taskModel):
    await taskModel.task.run()
    notify("All tasks completed")


async def disable_task(taskModel):
    def f(task):
        task.task.status = TaskStatus.DISABLED

    tasks_apply(taskModel, f)


async def enable_task(taskModel):
    def f(taskModel):
        taskModel.task.status = TaskStatus.NOT_STARTED

    tasks_apply(taskModel, f)


async def execute_command(model):
    logger.info(f"run command: {model.selectedTask.taskIndex=}, {model.commandText=}")
    match model.commandText.lower():
        case "disable":
            await disable_task(model.selectedTask)
    match model.commandText.lower():
        case "enable":
            await enable_task(model.selectedTask)


async def process_input(stdscr, model: TasksModel):
    stdscr.nodelay(True)

    model.inputMode = InputMode.NONE
    model.selectedTaskText = ""
    model.commandText = ""

    while True:
        with suppress(curses.error):
            k = stdscr.getkey()
            match model.inputMode:
                case InputMode.NONE:
                    if k == ":":
                        model.inputMode = InputMode.GET_TASK
                        model.selectedTaskText = ""
                        model.commandText = ""
                    if k.lower() == "s":
                        asyncio.create_task(start_tasks(model.rootTask))
                    if k.lower() == "x":
                        return

                case InputMode.GET_TASK:
                    if k == "\n":
                        model.selectTask(model.selectedTaskText)
                        if model.selectedTask:
                            model.inputMode = InputMode.GET_COMMAND
                        else:
                            model.inputMode = InputMode.NONE
                    else:
                        model.selectedTaskText += k

                case InputMode.GET_COMMAND:
                    if k.lower() == "d":
                        model.commandText = "disable"
                        await execute_command(model)
                        model.selectedTaskText = ""
                        model.commandText = ""
                        model.inputMode = InputMode.NONE
                    if k.lower() == "e":
                        model.commandText = "enable"
                        await execute_command(model)
                        model.selectedTaskText = ""
                        model.commandText = ""
                        model.inputMode = InputMode.NONE

            model.hasUpdates = True
        await asyncio.sleep(0.1)
