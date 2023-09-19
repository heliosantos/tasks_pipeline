import logging
import asyncio
import re

from .base_task import BaseTask
from .task_status import TaskStatus


logger = logging.getLogger('tasks_pipeline')


class RunProcessTask(BaseTask):

    def __init__(self, name, cmd=None, expectedOutput=None):
        super().__init__(name)
        if not cmd:
            raise TypeError('cmd expected 1 argument, got 0')
        self.cmd = cmd
        self.expectedOutput = expectedOutput

    async def run(self):
        await super().run()

        proc = await asyncio.create_subprocess_shell(
            self.cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        stdout, stderr = await proc.communicate()

        if stdout:
            logger.debug(stdout.decode())

        if stderr:
            logger.error(stderr.decode())

        if stderr:
            self.message = stderr.decode().replace('\r', '').replace('\n', ' ')
            await super().complete(TaskStatus.ERROR)
            return

        if self.expectedOutput and not stdout:
            self.message = 'no output'
            await super().complete(TaskStatus.ERROR)
            return

        if self.expectedOutput and not re.search(self.expectedOutput, stdout.decode().strip()):
            self.message = 'unexpected output'
            logger.error(stdout.decode())
            await super().complete(TaskStatus.ERROR)
            return

        await super().complete()
