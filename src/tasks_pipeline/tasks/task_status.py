from enum import Enum, auto


class TaskStatus(Enum):
    NOT_STARTED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    ERROR = auto()
    DISABLED = auto()
