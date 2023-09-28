import asyncio
import datetime
from itertools import zip_longest

from .base_task import BaseTask
from .task_status import TaskStatus


class WaitForTask(BaseTask):
    def __init__(self, name, waitFor: datetime.timedelta | str | int):
        super().__init__(name)
        self.waitFor = waitFor
        if isinstance(waitFor, str | int):
            waitFor = datetime.timedelta(seconds=int(waitFor))

    async def run(self):
        await super().run()

        waitUntil = datetime.datetime.now() + self.waitFor

        while waitUntil > datetime.datetime.now():
            if self.status == TaskStatus.CANCELLED:
                break
            elapsed = waitUntil - datetime.datetime.now()
            self.message = 'remaining: ' + str(elapsed).split('.')[0]
            await asyncio.sleep(0.1)
        else:
            await super().complete()

    async def cancel(self):
        await super().cancel()


class WaitUntilTask(BaseTask):
    def __init__(self, name, waitUntil: datetime.datetime | str = None):
        super().__init__(name)
        self.waitUntil = waitUntil

    async def run(self):
        await super().run()

        if isinstance(self.waitUntil, str):
            d = datetime.datetime.now()
            h, m, s = list(
                reversed(
                    [
                        int(x) if x is not None else None
                        for _, x in zip_longest(range(3), reversed(self.waitUntil.split(':')))
                    ]
                )
            )
            d1 = d.replace(
                hour=h if h is not None else d.hour,
                minute=m if m is not None else d.minute,
                second=s if s is not None else d.second,
                microsecond=0,
            )
            if d1 < d:
                for x, extra in zip([s, m, h, None], [1, 60, 3600, 86400]):
                    if x is None:
                        d1 = d1 + datetime.timedelta(seconds=extra)
                        break
            self.waitUntil = d1

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
