import asyncio
from .base_task import BaseTask


class ParallelTask(BaseTask):

    def __init__(self, name, tasks=[]):
        super().__init__(name)
        self.status = 'not started'
        self.tasks = tasks

    async def run(self):
        await super().run()
        self.status = 'running'
        await asyncio.gather(*[task.run() for task in self.tasks])

        await super().complete()
        self.status = 'completed'
