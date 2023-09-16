import asyncio
import datetime

from .base_task import BaseTask
from .task_status import TaskStatus


class WaitTask(BaseTask):

    def __init__(self, name, waitUntil: datetime.datetime = None, waitFor: datetime.timedelta = None):
        super().__init__(name)
        self.waitUntil = waitUntil
        self.waitFor = waitFor

    async def run(self):
        await super().run()

        if not self.waitUntil:
            self.waitUntil = datetime.datetime.now() + self.waitFor

        while self.waitUntil > datetime.datetime.now():
            if self.status == TaskStatus.CANCELLED:
                break
            elapsed = self.waitUntil - datetime.datetime.now()
            self.message = 'remaining: ' + str(elapsed).split('.')[0]
            await asyncio.sleep(0.1)
        else:
            await super().complete()

    async def cancel(self):
        await super().cancel()


class WaitUntilTask(WaitTask):

    def __init__(self, name, waitUntil: datetime.datetime):
        super().__init__(name, waitUntil=waitUntil)


class WaitForTask(WaitTask):

    def __init__(self, name, waitFor: datetime.timedelta | str | int):
        if isinstance(waitFor, str | int):
            waitFor = datetime.timedelta(seconds=int(waitFor))
        super().__init__(name, waitFor=waitFor)
