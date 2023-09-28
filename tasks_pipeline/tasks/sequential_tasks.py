from .base_task import BaseTask
from .task_status import TaskStatus


class SequentialTask(BaseTask):
    def __init__(self, name, tasks=[]):
        super().__init__(name)
        self.tasks = tasks

    async def run(self):
        await super().run()

        for task in self.tasks:
            if task.status == TaskStatus.DISABLED:
                continue
            await task.run()
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.DISABLED):
                await super().complete(TaskStatus.ERROR)
                break
        else:
            await super().complete()
