import asyncio
import curses
import importlib
import sys

from .tasks_logger import setup_loggers
from .view import display
from .controller import process_input
from .tasks_model import TasksModel
from .task_model import TaskModel
from .config import load_config


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

    config = load_config(sys.argv[1])

    setup_loggers(config.get("logging"))

    rootTask = config["rootTask"]
    title = config.setdefault("title", "Tasks Pipeline")

    rootTaskModel = create_task_model(rootTask)

    model = TasksModel(rootTaskModel)

    asyncio.create_task(display(stdscr, model, title))
    await process_input(stdscr, model)

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
