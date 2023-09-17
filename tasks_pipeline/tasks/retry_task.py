import asyncio

from .base_task import BaseTask
from .task_status import TaskStatus


class RetryTask(BaseTask):

    def __init__(self, name, maxRetries=1, delayBetweenRetries=0):
        super().__init__(name)
        self.maxRetries = maxRetries
        self.delayBetweenRetries = delayBetweenRetries
        self.tasks = []

    async def run(self):
        await super().run()

        task = self.tasks[0]

        for i in range(self.maxRetries):
            self.message = f'attempt {i + 1} out of {self.maxRetries}'
            await task.run()
            if task.status == TaskStatus.COMPLETED:
                await super().complete()
                return
            await asyncio.sleep(int(self.delayBetweenRetries))

        await super().complete(TaskStatus.ERROR)
