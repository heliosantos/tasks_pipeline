import asyncio
from .base_task import BaseTask


class ParallelTask(BaseTask):

    def __init__(self, name, tasks=[]):
        super().__init__(name)
        self.tasks = tasks

    async def run(self):
        await super().run()
        await asyncio.gather(*[task.run() for task in self.tasks])
        await super().complete()
