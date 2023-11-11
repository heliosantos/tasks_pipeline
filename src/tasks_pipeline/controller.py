from contextlib import suppress
import curses
import asyncio
import logging

from .tasks import TaskStatus
from .pipeline_model import PipelineModel, InputMode
from .util import tasks_apply
from .view import notify


logger = logging.getLogger("tasks_pipeline.controller")


async def start_tasks(taskModel):
    logger.info(f"start task: {taskModel.taskIndex=}, {taskModel.name=}")
    await taskModel.task.run()
    notify("All tasks completed")


async def disable_task(taskModel):
    logger.info(f"disable task: {taskModel.taskIndex=}, {taskModel.name=}")

    def f(task):
        task.task.status = TaskStatus.DISABLED

    tasks_apply(taskModel, f)


async def enable_task(taskModel):
    logger.info(f"enable task: {taskModel.taskIndex=}, {taskModel.name=}")

    def f(taskModel):
        taskModel.task.status = TaskStatus.NOT_STARTED

    tasks_apply(taskModel, f)


async def cancel_task(taskModel):
    def f(taskModel):
        if taskModel.task.status == TaskStatus.RUNNING:
            asyncio.create_task(taskModel.task.cancel())

    tasks_apply(taskModel, f)


async def process_input(stdscr, model: PipelineModel):
    stdscr.nodelay(True)

    model.inputMode = InputMode.NONE
    model.selectedTaskText = ""

    while True:
        with suppress(curses.error):
            k = stdscr.getkey()
            match model.inputMode:
                case InputMode.NONE:
                    if k == ":":
                        model.inputMode = InputMode.GET_TASK
                        model.selectedTaskText = ""
                    elif k.lower() == "s":
                        asyncio.create_task(start_tasks(model.rootTask))
                    elif k.lower() == "x":
                        return
                    elif k == "KEY_DOWN":
                        model.scrollDown()
                    elif k == "KEY_UP":
                        model.scrollUp()

                case InputMode.GET_TASK:
                    if k == "\n":
                        if model.selectedTaskText.isnumeric():
                            model.selectTask(model.selectedTaskText)
                            if model.selectedTask:
                                model.inputMode = InputMode.GET_COMMAND
                            else:
                                model.inputMode = InputMode.NONE
                        else:
                            model.inputMode = InputMode.NONE
                    if ord(k) == 8:  # back
                        model.selectedTaskText = model.selectedTaskText[:-1]
                    else:
                        model.selectedTaskText += k

                case InputMode.GET_COMMAND:
                    if k.lower() == "d":
                        await disable_task(model.selectedTask)
                        model.selectedTaskText = ""
                        model.inputMode = InputMode.NONE
                    if k.lower() == "e":
                        await enable_task(model.selectedTask)
                        model.selectedTaskText = ""
                        model.inputMode = InputMode.NONE
                    if k.lower() == "s":
                        asyncio.create_task(start_tasks(model.selectedTask))
                        model.selectedTaskText = ""
                        model.inputMode = InputMode.NONE
                    if k.lower() == "c":
                        asyncio.create_task(cancel_task(model.selectedTask))
                        model.selectedTaskText = ""
                        model.inputMode = InputMode.NONE

            model.hasUpdates = True
        await asyncio.sleep(0.1)
