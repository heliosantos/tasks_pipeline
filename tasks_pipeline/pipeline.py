import asyncio
import curses
import yaml
import importlib
import sys

try:
    import win11toast

    toastAvailable = True
except ModuleNotFoundError:
    toastAvailable = False

from .tasks import TaskStatus
from .tasks_logger import setup_loggers
from .util import tasks_apply
from .view import display
from .controller import process_input
from .tasks_model import TasksModel
from .task_model import TaskModel


taskIndex = 0

defaultNames = {
    "SequentialTask": "⭣",
    "ParallelTask": "⮆",
    "RetryTask": "↻",
}


def create_task_model(task, parentTaskModel=None):
    global taskIndex
    taskIndex += 1
    t = task["type"]
    t = t.split(".")
    if len(t) == 1:
        t = ["tasks_pipeline"] + t
    mod, cls = t
    mod = importlib.import_module(mod)
    cls = getattr(mod, cls)

    taskName = task.get("name", "")
    if defaultName := defaultNames.get(task["type"], ""):
        taskName = f"{defaultName} {taskName}"

    taskModel = TaskModel(taskName, cls(taskName, **task.get("params", {})), taskIndex=taskIndex)

    if parentTaskModel:
        parentTaskModel.subtasks.append(taskModel)
        parentTaskModel.task.tasks.append(taskModel.task)

    for child in task.get("tasks", []):
        create_task_model(child, taskModel)

    return taskModel


async def main(stdscr):
    if len(sys.argv) < 2:
        print("usage: tasks_pipeline configFile")
        return

    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)

    with open(sys.argv[1], "rb") as f:
        config = yaml.safe_load(f.read().decode("utf-8"))

    setup_loggers(config.get("logging"))

    rootTask = config["rootTask"]
    title = config.get("title", "Tasks Pipeline")

    rootTaskModel = create_task_model(rootTask)

    cancelAllTasks = False

    async def cancel_all_tasks():
        nonlocal cancelAllTasks
        await cancel_task()
        cancelAllTasks = True

    async def cancel_task():
        futures = []

        def cancel(taskModel):
            if taskModel.task.status == TaskStatus.RUNNING:
                futures.append(taskModel.task.cancel())

        tasks_apply(rootTask, cancel)
        await asyncio.gather(*futures)

    async def start_tasks():
        await rootTaskModel.task.run()
        if toastAvailable and config.get("systemNotification", True):
            win11toast.notify(
                title,
                "All tasks completed",
            )

    model = TasksModel(rootTaskModel)

    asyncio.create_task(display(stdscr, model, title))
    await process_input(stdscr, model, cancel_all_tasks, start_tasks)

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()


def main_curses_wrapper(stdscr):
    asyncio.run(main(stdscr))


def run():
    curses.wrapper(main_curses_wrapper)


if __name__ == "__main__":
    run()
