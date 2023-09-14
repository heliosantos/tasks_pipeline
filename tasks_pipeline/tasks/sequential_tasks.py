from .base_task import BaseTask


class SequentialTask(BaseTask):

    def __init__(self, name, tasks=[]):
        super().__init__(name)
        self.status = 'not started'
        self.tasks = tasks

    async def run(self):
        await super().run()
        self.status = 'running'

        for task in self.tasks:
            await task.run()

        await super().complete()
        self.status = 'completed'
