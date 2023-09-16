from .base_task import BaseTask


class SequentialTask(BaseTask):

    def __init__(self, name, tasks=[]):
        super().__init__(name)
        self.tasks = tasks

    async def run(self):
        await super().run()

        for task in self.tasks:
            await task.run()

        await super().complete()
