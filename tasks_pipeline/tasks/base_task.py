from .task_status import TaskStatus
import datetime


class BaseTask(object):

    def __init__(self, name):
        self.name = name
        self.operatingStatus = TaskStatus.NOT_STARTED
        self.status = ''
        self.message = ''
        self.startTime = None
        self.stopTime = None

    async def run(self):
        self.operatingStatus = TaskStatus.RUNNING
        self.startTime = datetime.datetime.now()

    async def cancel(self):
        self.operatingStatus = TaskStatus.CANCELLED
        self.stopTime = datetime.datetime.now()

    async def complete(self, status=TaskStatus.COMPLETED):
        self.operatingStatus = status
        self.stopTime = datetime.datetime.now()
