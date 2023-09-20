import asyncio
import curses
import datetime
from contextlib import suppress
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


def trim_text(text, maxLen):
    text = text.ljust(maxLen)
    if len(text) <= maxLen:
        return text
    return text[:maxLen - 3] + '...'


def scale_color(r, g, b):
    f = (curses.COLORS - 1) / 255
    rgb = (
        min(round(r * f), curses.COLORS - 1),
        min(round(g * f), curses.COLORS - 1),
        min(round(b * f),  curses.COLORS - 1),
        )
    return rgb


colorCounter = 0


def get_color(r, g, b):
    global colorCounter
    colorCounter += 1
    r, g, b = scale_color(r, g, b)
    curses.init_color(colorCounter, *scale_color(r, g, b))
    curses.init_pair(colorCounter, colorCounter, -1)
    return curses.color_pair(colorCounter)


async def display(stdscr, rootTask, title):
    tasks = flatten_tasks(rootTask)
    add_display_info(rootTask)

    width = curses.COLS

    c_gray = get_color(192, 192, 192)
    c_green = get_color(0, 255, 0)
    c_red = get_color(255, 0, 0)
    c_lightgray = get_color(240, 240, 240)
    c_orange = get_color(255, 165, 0)
    # c_light = get_color(240, 240, 240)

    stdscr.addstr(1, 3, title, c_gray)
    stdscr.addstr(4 + len(tasks) + 1, 3, '[S] Start, [C] Cancel all Tasks, [X] exit', c_gray)

    for i, task in enumerate(tasks):
        task['win'] = curses.newwin(1, width - 1 - 3, i + 4, 3)

    nameLen = min(max(len(t['displayPrefix'] + t['name']) for t in tasks), 20)
    elapsedLen = 8
    statusLen = 12
    msgLen = width - nameLen - elapsedLen - statusLen - 9

    stdscr.addstr(3, 3,
                  trim_text('Task', nameLen) + ' ' +
                  trim_text('Elapsed', elapsedLen) + ' ' +
                  trim_text('Status', statusLen) + ' ' +
                  trim_text('Message', msgLen), c_gray)

    stdscr.refresh()

    while True:

        for task in tasks:
            taskInstance = task['instance']
            now = datetime.datetime.now()
            elapsed = (taskInstance.stopTime or now) - (taskInstance.startTime or now)

            taskColor = (c_gray if taskInstance.status == TaskStatus.NOT_STARTED else
                         c_lightgray if taskInstance.status == TaskStatus.RUNNING else
                         c_green if taskInstance.status == TaskStatus.COMPLETED else
                         c_red)

            task['win'].clear()

            dp = task['displayPrefix']
            fn = trim_text(dp + task['name'], nameLen).removeprefix(dp)

            for t, c in (
                (dp, c_gray),
                (fn + ' ', taskColor),
                (trim_text(str(elapsed).split('.')[0] + ' ', elapsedLen), c_lightgray),
                (trim_text(taskInstance.status.name.replace('NOT_STARTED', '') + ' ', statusLen), c_orange),
                (trim_text(taskInstance.message + ' ', msgLen), c_lightgray)
            ):
                task['win'].addstr(t, c)

            task['win'].refresh()

        await asyncio.sleep(0.1)


async def process_input(stdscr, cancel_all_tasks, start_tasks):
    stdscr.nodelay(True)
    while True:
        with suppress(curses.error):
            k = stdscr.getkey()
            if k.lower() == 'c':
                await cancel_all_tasks()
            if k.lower() == 's':
                asyncio.create_task(start_tasks())
            if k.lower() == 'x':
                return

        await asyncio.sleep(1)


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


def add_display_info(node, level=0, parentPrefix='', lastChild=True):
    prefix = ''
    childrenPrefix = ''
    if level == 0:
        prefix = ''
        childrenPrefix = ''
    else:
        prefix = parentPrefix + ('└' if lastChild else '├')
        childrenPrefix = parentPrefix + (' ' if lastChild else '│')

    node['displayPrefix'] = prefix

    children = node.get('tasks', [])

    if children:
        lastChildIdx = len(children) - 1
        for e, child in enumerate(children):
            add_display_info(child, level + 1, childrenPrefix, e == lastChildIdx)


def flatten_tasks(task):
    tasks = []
    tasks.append(task)
    for child in task.get('tasks', []):
        tasks.extend(flatten_tasks(child))
    return tasks


def tasks_apply(task, f):
    f(task)
    for child in task.get('tasks', []):
        tasks_apply(child, f)


async def main():
    if len(sys.argv) < 2:
        print('usage: tasks_pipeline configFile')
        return

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)

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

    asyncio.create_task(display(stdscr, rootTask, title))
    await process_input(stdscr, cancel_all_tasks, start_tasks)

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()


if __name__ == '__main__':
    asyncio.run(main())
