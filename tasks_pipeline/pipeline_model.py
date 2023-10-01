import importlib
from enum import Enum, auto

from .util import flatten_tasks
from .task_model import TaskModel


class InputMode(Enum):
    NONE = auto()
    GET_TASK = auto()
    GET_COMMAND = auto()


class PipelineModel:
    def __init__(self, config):
        self.load_config(config)

    def selectTask(self, key):
        matching = list(filter(lambda t: t.taskIndex == int(key), self.tasks))
        self.selectedTask = matching[0] if matching else None

    def load_config(self, config=None):
        if config:
            self.config = config

        self.rootTask = create_task_models(self.config["rootTask"])
        self.tasks = flatten_tasks(self.rootTask)
        self.title = self.config.get('title', 'Tasks Pipeline')
        self.inputMode: InputMode = InputMode.NONE
        self.hasUpdates: bool = True
        self.selectedTask = None
        self.selectedTaskText = ""


def create_task_models(rootTask):
    taskIndex = 0

    defaultNames = {
        "SequentialTask": "⭣",
        "ParallelTask": "⮆",
        "RetryTask": "↻",
    }

    def create_task_model(task, parentTaskModel=None):
        nonlocal taskIndex
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

    return create_task_model(rootTask)
