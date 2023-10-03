import asyncio
import curses
import datetime
import math
from statistics import median

from .color_manager import ColorManager


try:
    import win11toast

    toastAvailable = True
except ModuleNotFoundError:
    toastAvailable = False

from .tasks import TaskStatus
from .pipeline_model import InputMode, PipelineModel
from .config import get_config


class ScreenRenderer:
    def __init__(self, stdscr, model: PipelineModel):
        self.stdscr = stdscr
        self.init_colors()
        self.maxy = None
        self.maxx = None
        self.taskStartIndex = 0
        self.hasHiddentTasks = False

        self.update(model)

    def init_colors(self):
        self.colors = ColorManager.instance()
        self.colors.get_color(255, 0, 0, "red")
        self.colors.get_color(240, 240, 240, "light grey")
        self.colors.get_color(192, 192, 192, "grey")
        self.colors.get_color(32, 32, 32, "dark grey")
        self.colors.get_color(0, 255, 0, "green")
        self.colors.get_color(255, 165, 0, "orange")
        self.colors.get_color(240, 240, 240, "light")

    def update(self, model: PipelineModel | None = None):
        if model:
            self.model = model
        self.maxy, self.maxx = self.stdscr.getmaxyx()
        if self.maxy < 6:
            win = self.lines[0]
            win.clear()
            win.addstr("The screen is too samll")
            win.refresh()
            return
        self.lines = [curses.newwin(1, self.maxx, i, 0) for i in range(self.maxy)]
        self._showTitle()
        self._updateScroll()
        self._showTasks()
        self._showOptions()

    def _showTitle(self):
        color = self.colors.get("grey")

        win = self.lines[0]
        win.clear()
        win.addstr(self.model.title, color)
        win.refresh()

    def _numVisibleTasks(self):
        maxTasks = self.maxy - 6
        return min(maxTasks, len(self.model.tasks))

    def _showTasks(self):
        screenTaskStart = 3

        numVisibleTasks = self._numVisibleTasks()
        visibleTasks = self.model.tasks[self.taskStartIndex : self.taskStartIndex + numVisibleTasks]
        taskWin = self.lines[screenTaskStart : screenTaskStart + numVisibleTasks]

        nameLen = min(max(len(t.displayPrefix + t.name) for t in self.model.tasks), 20)
        elapsedLen = 8
        statusLen = 12
        msgLen = self.maxx - nameLen - elapsedLen - statusLen - 9

        showNumbers = self.model.inputMode in (InputMode.GET_TASK, InputMode.GET_COMMAND)
        numLinesWidth = (int(math.log10(visibleTasks[-1].taskIndex + 1)) + 1) if showNumbers else 0

        self.lines[2].addstr(
            " " * (numLinesWidth + 1 if numLinesWidth else 0)
            + trim_text("Task", nameLen)
            + " "
            + trim_text("Elapsed", elapsedLen)
            + " "
            + trim_text("Status", statusLen)
            + " "
            + trim_text("Message", msgLen),
        )
        self.lines[2].refresh()

        for win, taskModel in zip(taskWin, visibleTasks):
            self._showTask(taskModel, win, numLinesWidth, nameLen, elapsedLen, statusLen, msgLen)

    def _showTask(self, taskModel, win, numLinesWidth, nameLen, elapsedLen, statusLen, msgLen):
        task = taskModel.task
        now = datetime.datetime.now()
        elapsed = (task.stopTime or now) - (task.startTime or now)

        taskColor = (
            self.colors.get("grey")
            if task.status == TaskStatus.NOT_STARTED
            else self.colors.get("dark grey")
            if task.status == TaskStatus.DISABLED
            else self.colors.get("light grey")
            if task.status == TaskStatus.RUNNING
            else self.colors.get("green")
            if task.status == TaskStatus.COMPLETED
            else self.colors.get("red")
        )

        win.clear()

        dp = taskModel.displayPrefix
        fn = trim_text(dp + taskModel.name, nameLen).removeprefix(dp)

        columns = []

        if numLinesWidth > 0:
            lineNumberColor = (
                self.colors.get("orange")
                if (self.model.selectedTask and taskModel.taskIndex == self.model.selectedTask.taskIndex)
                else self.colors.get("light grey")
            )
            columns.append((str(taskModel.taskIndex).rjust(numLinesWidth - 1) + " ", lineNumberColor))
        columns.extend(
            [
                (dp, self.colors.get("grey")),
                (fn + " ", taskColor),
                (trim_text(str(elapsed).split(".")[0] + " ", elapsedLen), self.colors.get("light grey")),
                (
                    trim_text(task.status.name.replace("NOT_STARTED", "").replace("DISABLED", "") + " ", statusLen),
                    self.colors.get("orange"),
                ),
                (
                    trim_text(task.message + " ", (msgLen - numLinesWidth) if numLinesWidth > 0 else msgLen),
                    self.colors.get("light grey"),
                ),
            ]
        )

        for t, c in columns:
            win.addstr(t, c)
        win.refresh()

    def _showOptions(self):
        numVisibleTasks = self._numVisibleTasks()
        win = self.lines[3 + numVisibleTasks + 1]
        win.clear()
        options = []
        match self.model.inputMode:
            case InputMode.NONE:
                options.append("[S] Start")
                options.append("[X] exit")
                if numVisibleTasks < len(self.model.tasks):
                    options.append("[↑] scroll up")
                    options.append("[↓] scroll down")

            case InputMode.GET_TASK:
                options.append(f"task index: {self.model.selectedTaskText}")

            case InputMode.GET_COMMAND:
                if self.model.selectedTask.task.status != TaskStatus.DISABLED:
                    options.append("[D] Disable")
                else:
                    options.append("[E] enable")
                if self.model.selectedTask.task.status == TaskStatus.RUNNING:
                    options.append("[C] cancel")

        win.addstr("   ".join(options))

        win.refresh()

    def _updateScroll(self):
        if self.model.scroll:
            self.taskStartIndex = median(
                [0, self.taskStartIndex + self.model.scroll, len(self.model.tasks) - self._numVisibleTasks()]
            )
            self.model.scroll = 0


def notify(message):
    config = get_config()
    if toastAvailable and config.get("systemNotification", True):
        win11toast.notify(
            config["title"],
            message,
        )


def trim_text(text, maxLen):
    text = text.ljust(maxLen)
    if len(text) <= maxLen:
        return text
    return text[: maxLen - 3] + "..."


async def display(stdscr, model: PipelineModel):
    sr = ScreenRenderer(stdscr, model)
    while True:
        sr.update()
        await asyncio.sleep(0.1)
