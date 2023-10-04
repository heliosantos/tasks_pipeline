from .tasks import TaskStatus


class TaskModel:
    def __init__(self, name, task, taskIndex=None):
        self.task = task
        self.parentTask = None
        self.subtasks = []
        self.taskIndex = taskIndex
        self.displayPrefix = ""
        self.win = None
        self.name = name

    def get_ancestry_disabled_status(self):
        enabledStatus = [self.task.status == TaskStatus.DISABLED]

        if self.parentTask:
            enabledStatus.extend(self.parentTask.get_ancestry_disabled_status())

        return enabledStatus
