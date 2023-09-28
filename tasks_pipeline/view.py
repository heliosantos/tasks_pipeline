import asyncio
import curses
import datetime
from .tasks import TaskStatus
from .tasks_model import InputMode, TasksModel


def add_display_info(taskModel, level=0, parentPrefix="", lastChild=True):
    prefix = ""
    childrenPrefix = ""
    if level == 0:
        prefix = ""
        childrenPrefix = ""
    else:
        prefix = parentPrefix + ("└" if lastChild else "├")
        childrenPrefix = parentPrefix + (" " if lastChild else "│")

    taskModel.displayPrefix = prefix

    if taskModel.subtasks:
        lastChildIdx = len(taskModel.subtasks) - 1
        for e, child in enumerate(taskModel.subtasks):
            add_display_info(child, level + 1, childrenPrefix, e == lastChildIdx)


def trim_text(text, maxLen):
    text = text.ljust(maxLen)
    if len(text) <= maxLen:
        return text
    return text[: maxLen - 3] + "..."


def scale_color(r, g, b):
    f = (curses.COLORS - 1) / 255
    rgb = (
        min(round(r * f), curses.COLORS - 1),
        min(round(g * f), curses.COLORS - 1),
        min(round(b * f), curses.COLORS - 1),
    )
    return rgb


colorCounter = 0


def get_color(r, g, b):
    global colorCounter
    colorCounter += 1
    r, g, b = scale_color(r, g, b)
    curses.init_color(colorCounter, *scale_color(r, g, b))
    curses.init_pair(colorCounter, colorCounter, -1)
    return curses.color_pair(colorCounter)


async def input_update(stdscr, model: TasksModel):
    width = curses.COLS
    win = curses.newwin(1, width - 1 - 3, 4 + len(model.tasks) + 1, 3)

    while True:
        if not model.hasUpdates:
            await asyncio.sleep(0.1)
            continue
        win.clear()
        match model.inputMode:
            case InputMode.NONE:
                win.addstr("[S] Start, [X] exit")
            case InputMode.GET_TASK:
                win.addstr(f"enter task index: {model.selectedTaskText}")
            case InputMode.GET_COMMAND:
                text = f"task index: {model.selectedTask.taskIndex}   "
                text = "[D] Disable" if model.selectedTask.task.status != TaskStatus.DISABLED else "[E] enable"
                win.addstr(text)

        win.refresh()
        model.hasUpdates = False


async def display(stdscr, model: TasksModel, title):
    add_display_info(model.rootTask)

    numLinesWidth = len(str(model.tasks[-1].taskIndex)) + 1

    width = curses.COLS

    c_lightgray = get_color(240, 240, 240)
    c_gray = get_color(192, 192, 192)
    c_darkgray = get_color(32, 32, 32)
    c_green = get_color(0, 255, 0)
    c_red = get_color(255, 0, 0)
    c_orange = get_color(255, 165, 0)
    # c_light = get_color(240, 240, 240)

    stdscr.addstr(1, 3, title, c_gray)
    asyncio.create_task(input_update(stdscr, model))

    for i, taskModel in enumerate(model.tasks):
        taskModel.win = curses.newwin(1, width - 1 - 3, i + 4, 3)

    nameLen = min(max(len(t.displayPrefix + t.name) for t in model.tasks), 20)
    elapsedLen = 8
    statusLen = 12
    msgLen = width - nameLen - elapsedLen - statusLen - 9

    stdscr.addstr(
        3,
        3,
        trim_text("Task", nameLen)
        + " "
        + trim_text("Elapsed", elapsedLen)
        + " "
        + trim_text("Status", statusLen)
        + " "
        + trim_text("Message", msgLen),
        c_gray,
    )

    stdscr.refresh()

    while True:
        showNumbers = model.inputMode in (InputMode.GET_TASK, InputMode.GET_COMMAND)
        for taskModel in model.tasks:
            task = taskModel.task
            now = datetime.datetime.now()
            elapsed = (task.stopTime or now) - (task.startTime or now)

            taskColor = (
                c_gray
                if task.status == TaskStatus.NOT_STARTED
                else c_darkgray
                if task.status == TaskStatus.DISABLED
                else c_lightgray
                if task.status == TaskStatus.RUNNING
                else c_green
                if task.status == TaskStatus.COMPLETED
                else c_red
            )

            taskModel.win.clear()

            dp = taskModel.displayPrefix
            fn = trim_text(dp + taskModel.name, nameLen).removeprefix(dp)

            columns = []

            if showNumbers:
                lineNumberColor = (
                    c_orange
                    if (model.selectedTask and taskModel.taskIndex == model.selectedTask.taskIndex)
                    else c_lightgray
                )
                columns.append((str(taskModel.taskIndex).rjust(numLinesWidth - 1) + " ", lineNumberColor))
            columns.extend(
                [
                    (dp, c_gray),
                    (fn + " ", taskColor),
                    (trim_text(str(elapsed).split(".")[0] + " ", elapsedLen), c_lightgray),
                    (
                        trim_text(task.status.name.replace("NOT_STARTED", "").replace("DISABLED", "") + " ", statusLen),
                        c_orange,
                    ),
                    (trim_text(task.message + " ", (msgLen - numLinesWidth) if showNumbers else msgLen), c_lightgray),
                ]
            )

            for t, c in columns:
                taskModel.win.addstr(t, c)

            taskModel.win.refresh()

        await asyncio.sleep(0.1)
