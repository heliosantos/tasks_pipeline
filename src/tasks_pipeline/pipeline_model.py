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
        self.scroll = 0

    def selectTask(self, key):
        matching = list(filter(lambda t: t.taskIndex == int(key), self.tasks))
        self.selectedTask = matching[0] if matching else None

    def load_config(self, config=None):
        if config:
            self.config = config

        self.rootTask = create_task_models(self.config['rootTask'])
        add_display_info(self.rootTask)

        self.tasks = flatten_tasks(self.rootTask)
        self.title = self.config.get('title', 'Tasks Pipeline')
        self.inputMode: InputMode = InputMode.NONE
        self.hasUpdates: bool = True
        self.selectedTask = None
        self.selectedTaskText = ''

    def scrollDown(self):
        self.scroll = 1

    def scrollUp(self):
        self.scroll = -1


def create_task_models(rootTask):
    taskIndex = 0

    defaultNames = {
        'SequentialTask': '⭣',
        'ParallelTask': '⮆',
        'RetryTask': '↻',
    }

    def create_task_model(task, parentTaskModel=None):
        nonlocal taskIndex
        taskIndex += 1
        t = task['type']
        t = t.split('.')
        if len(t) == 1:
            t = ['tasks_pipeline'] + t
        mod, cls = t
        mod = importlib.import_module(mod)
        cls = getattr(mod, cls)

        taskName = task.get('name', '')
        if defaultName := defaultNames.get(task['type'], ''):
            taskName = f'{defaultName} {taskName}'

        taskModel = TaskModel(taskName, cls(taskName, **task.get('params', {})), taskIndex=taskIndex)

        if parentTaskModel:
            taskModel.parentTask = parentTaskModel
            parentTaskModel.subtasks.append(taskModel)
            parentTaskModel.task.tasks.append(taskModel.task)

        for child in task.get('tasks', []):
            create_task_model(child, taskModel)

        return taskModel

    return create_task_model(rootTask)


def add_display_info(taskModel, level=0, parentPrefix='', lastChild=True):
    prefix = ''
    childrenPrefix = ''
    if level == 0:
        prefix = ''
        childrenPrefix = ''
    else:
        prefix = parentPrefix + ('└' if lastChild else '├')
        childrenPrefix = parentPrefix + (' ' if lastChild else '│')
    taskModel.displayPrefix = prefix

    if taskModel.subtasks:
        lastChildIdx = len(taskModel.subtasks) - 1
        for e, child in enumerate(taskModel.subtasks):
            add_display_info(child, level + 1, childrenPrefix, e == lastChildIdx)
