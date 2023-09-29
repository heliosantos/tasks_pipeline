from .task_status import TaskStatus
import datetime


class BaseTask(object):
    def __init__(self, name):
        self.name = name
        self.status = TaskStatus.NOT_STARTED
        self.message = ""
        self.startTime = None
        self.stopTime = None
        self.tasks = []

    async def run(self):
        self.status = TaskStatus.RUNNING
        self.startTime = datetime.datetime.now()

    async def cancel(self):
        for task in self.tasks:
            await task.cancel()
        self.status = TaskStatus.CANCELLED
        self.stopTime = datetime.datetime.now()

    async def complete(self, status=TaskStatus.COMPLETED):
        self.status = status
        self.stopTime = datetime.datetime.now()
