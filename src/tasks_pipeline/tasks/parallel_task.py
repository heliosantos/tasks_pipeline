import asyncio
from .base_task import BaseTask
from .task_status import TaskStatus


class ParallelTask(BaseTask):
    def __init__(self, name, maxConcurrency=None):
        super().__init__(name)
        self.maxConcurrency = maxConcurrency

    async def run(self):
        await super().run()

        if self.maxConcurrency:
            semaphore = asyncio.Semaphore(self.maxConcurrency)

            async def f(task):
                async with semaphore:
                    if self.status in (TaskStatus.DISABLED, TaskStatus.CANCELLED):
                        return
                    return await task.run()

        else:

            async def f(task):
                return await task.run()

        await asyncio.gather(
            *[f(task) for task in self.tasks if task.status not in (TaskStatus.DISABLED, TaskStatus.CANCELLED)]
        )

        if any((task for task in self.tasks if task.status not in (TaskStatus.COMPLETED, TaskStatus.DISABLED))):
            await super().complete(TaskStatus.ERROR)
        else:
            await super().complete()
