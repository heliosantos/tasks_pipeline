class TaskModel:
    def __init__(self, name, task, taskIndex=None):
        self.task = task
        self.subtasks = []
        self.taskIndex = taskIndex
        self.displayPrefix = ""
        self.win = None
        self.name = name
