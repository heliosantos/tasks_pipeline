from enum import Enum, auto

from .util import flatten_tasks


class InputMode(Enum):
    NONE = auto()
    GET_TASK = auto()
    GET_COMMAND = auto()


class TasksModel:
    def __init__(self, rootTask):
        self.rootTask = rootTask
        self.tasks = flatten_tasks(rootTask)
        self.inputMode: InputMode = InputMode.NONE
        self.hasUpdates: bool = True
        self.selectedTask = None
        self.selectedTaskText = ""
        self.commandText: str = ""

    def selectTask(self, key):
        matching = list(filter(lambda t: t.taskIndex == int(key), self.tasks))
        self.selectedTask = matching[0] if matching else None