import asyncio
from .base_task import BaseTask
from .task_status import TaskStatus


class ParallelTask(BaseTask):

    def __init__(self, name, maxConcurrency=None, tasks=[]):
        super().__init__(name)
        self.maxConcurrency = maxConcurrency
        self.tasks = tasks

    async def run(self):
        await super().run()

        if self.maxConcurrency:
            semaphore = asyncio.Semaphore(self.maxConcurrency)

            async def f(coro):
                async with semaphore:
                    return await coro
        else:
            async def f(coro):
                return await coro

        await asyncio.gather(*[f(task.run()) for task in self.tasks if task.status != TaskStatus.DISABLED])

        if any((task for task in self.tasks if task.status not in (TaskStatus.COMPLETED, TaskStatus.DISABLED))):
            await super().complete(TaskStatus.ERROR)
        else:
            await super().complete()
