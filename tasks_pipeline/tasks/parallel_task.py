import asyncio
from .base_task import BaseTask
from .task_status import TaskStatus


class ParallelTask(BaseTask):

    def __init__(self, name, tasks=[]):
        super().__init__(name)
        self.tasks = tasks

    async def run(self):
        await super().run()
        await asyncio.gather(*[task.run() for task in self.tasks])

        if any((task for task in self.tasks if task.status != TaskStatus.COMPLETED)):
            await super().complete(TaskStatus.ERROR)
        else:
            await super().complete()
