import logging
import socket

from .base_task import BaseTask
from .task_status import TaskStatus


logger = logging.getLogger("tasks_pipeline.port_connectivity_task")


class PortConnectivityTask(BaseTask):
    def __init__(self, name, hosts=[]):
        super().__init__(name)
        self.hosts = hosts

    async def run(self):
        await super().run()

        connected = 0
        for host in self.hosts:
            ipAddress, port = host.split(':')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex((ipAddress, int(port))) == 0:
                    connected += 1
                else:
                    logger.info(f'failed to connect to {ipAddress} on port {port}')

        self.message = f'connected {connected}/{len(self.hosts)}'
        if connected == len(self.hosts):
            await super().complete()
        else:
            await super().complete(TaskStatus.ERROR)
