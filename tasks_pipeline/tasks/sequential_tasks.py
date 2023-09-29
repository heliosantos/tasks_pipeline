from .base_task import BaseTask
from .task_status import TaskStatus


class SequentialTask(BaseTask):
    def __init__(self, name):
        super().__init__(name)

    async def run(self):
        await super().run()

        for task in self.tasks:
            if task.status == TaskStatus.DISABLED:
                continue
            if task.status == TaskStatus.CANCELLED:
                return
            await task.run()
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.DISABLED):
                await super().complete(TaskStatus.ERROR)
                break
        else:
            await super().complete()
