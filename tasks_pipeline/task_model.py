from enum import Enum, auto

from .util import flatten_tasks


class InputMode(Enum):
    NONE = auto()
    GET_TASK = auto()
    GET_COMMAND = auto()


class TaskModel:
    def __init__(self, rootTask):
        self.rootTask = rootTask
        self.tasks = flatten_tasks(rootTask)
        self.inputMode: InputMode = InputMode.NONE
        self.hasUpdates: bool = True
        self.selectedTask: int = 0
        self.command: str = ''
        add_task_index(self.tasks)


def add_task_index(tasks):
    for i, task in enumerate(tasks):
        task['index'] = i + 1
        # node['prettyLineNumber'] = str(node['lineNumber']).rjust(len(str(len(tasks))))
