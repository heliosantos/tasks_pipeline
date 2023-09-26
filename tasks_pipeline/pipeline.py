import asyncio
import curses
import yaml
import importlib
import sys

try:
    import win11toast
    toastAvailable = True
except ModuleNotFoundError:
    toastAvailable = False

from .tasks import TaskStatus
from .tasks_logger import setup_loggers
from .util import tasks_apply
from .view import display
from .controller import process_input
from .tasks_model import TasksModel


def instanciate_tasks(task):
    t = task['type']
    t = t.split('.')
    if len(t) == 1:
        t = ['tasks_pipeline'] + t
    mod, cls = t
    mod = importlib.import_module(mod)
    cls = getattr(mod, cls)

    task['instance'] = cls(task['name'], **task.get('params', {}))

    for child in task.get('tasks', []):
        instanciate_tasks(child)

    if 'tasks' in task['instance'].__dict__:
        task['instance'].tasks = [t['instance'] for t in task.get('tasks', [])]


async def main(stdscr):
    if len(sys.argv) < 2:
        print('usage: tasks_pipeline configFile')
        return

    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)

    with open(sys.argv[1], 'rb') as f:
        config = yaml.safe_load(f.read().decode('utf-8'))

    setup_loggers(config.get('logging'))

    rootTask = config['rootTask']
    title = config.get('title', 'Tasks Pipeline')

    def add_default_name(task):
        defaultNames = {
            'SequentialTask': '⭣',
            'ParallelTask': '⮆',
            'RetryTask': '↻',
        }
        if not task.get('name'):
            task['name'] = defaultNames.get(task['type'], task['type'])

    tasks_apply(rootTask, add_default_name)

    instanciate_tasks(rootTask)

    cancelAllTasks = False

    async def cancel_all_tasks():
        nonlocal cancelAllTasks
        await cancel_task()
        cancelAllTasks = True

    async def cancel_task():
        futures = []

        def cancel(task):
            instance = task['instance']
            if instance.status == TaskStatus.RUNNING:
                futures.append(instance.cancel())

        tasks_apply(rootTask, cancel)
        await asyncio.gather(*futures)

    async def start_tasks():
        await rootTask['instance'].run()
        if toastAvailable and config.get('systemNotification', True):
            win11toast.notify(
                title,
                'All tasks completed',
            )

    model = TasksModel(rootTask)

    asyncio.create_task(display(stdscr, model, title))
    await process_input(stdscr, model, cancel_all_tasks, start_tasks)

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()


def main_curses_wrapper(stdscr):
    asyncio.run(main(stdscr))


def run():
    curses.wrapper(main_curses_wrapper)


if __name__ == '__main__':
    run()
