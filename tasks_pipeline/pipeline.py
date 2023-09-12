import asyncio
import curses
import datetime
from contextlib import suppress
import os
import yaml
import importlib
import sys

from .tasks import TaskStatus


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


async def display(stdscr, rootTask):
    tasks = flatten_tasks(rootTask)
    add_display_info(rootTask)

    width = curses.COLS

    c_gray = get_color(192, 192, 192)
    c_green = get_color(0, 255, 0)
    c_red = get_color(255, 0, 0)
    c_lightgray = get_color(240, 240, 240)
    c_orange = get_color(255, 165, 0)
    # c_light = get_color(240, 240, 240)

    stdscr.addstr(1, 3, 'Tasks Pipeline', c_gray)
    stdscr.addstr(4 + len(tasks) + 1, 3, '[S] Start, [N] Next Task, [C] Cancel all Tasks, [X] exit', c_gray)

    for i, task in enumerate(tasks):
        task['win'] = curses.newwin(1, width - 1 - 3, i + 4, 3)

    nameLen = min(max(len(t['displayInfo']) for t in tasks), 20)
    elapsedLen = 8
    statusLen = 20
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

            taskColor = (c_gray if taskInstance.operatingStatus == TaskStatus.NOT_STARTED else
                         c_lightgray if taskInstance.operatingStatus == TaskStatus.RUNNING else
                         c_green if taskInstance.operatingStatus == TaskStatus.COMPLETED else
                         c_red)

            task['win'].clear()

            rowLen = 0
            for t, c in (
                (trim_text(task['displayInfo'], nameLen), taskColor),
                (trim_text(str(elapsed).split('.')[0], elapsedLen), c_lightgray),
                (trim_text(taskInstance.status, statusLen), c_orange),
                (trim_text(taskInstance.message, msgLen), c_lightgray)
            ):
                rowLen += len(t) + 1
                task['win'].addstr(t + ' ', c)

            task['win'].refresh()

        await asyncio.sleep(0.1)


async def process_input(stdscr, cancel_task, cancel_all_tasks, start_tasks):
    stdscr.nodelay(True)
    while True:
        with suppress(curses.error):
            k = stdscr.getkey()
            if k.lower() == 'c':
                await cancel_all_tasks()
            if k.lower() == 'n':
                await cancel_task()
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

    task['instance'] = cls(task['name'], *task.get('params', []))

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

    prefix += node['name']
    node['displayInfo'] = prefix

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
        print(f'usage: tasks_pipeline configFile')
        return

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)

    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)

    with open(sys.argv[1], 'rb') as f:
        task = yaml.safe_load(f.read().decode('utf-8'))['tasks']

    def add_default_name(task):
        defaultNames = {
            'SequentialTask': '⭣',
            'ParallelTask': '⮆',
        }
        if not task.get('name'):
            task['name'] = defaultNames.get(task['type'], task['type'])

    tasks_apply(task, add_default_name)

    instanciate_tasks(task)

    cancelAllTasks = False

    async def cancel_all_tasks():
        nonlocal cancelAllTasks
        await cancel_task()
        cancelAllTasks = True

    async def cancel_task():
        futures = []

        def cancel(task):
            instance = task['instance']
            if instance.operatingStatus == TaskStatus.RUNNING:
                futures.append(instance.cancel())

        tasks_apply(task, cancel)
        await asyncio.gather(*futures)

    async def start_tasks():
        await task['instance'].run()

    asyncio.create_task(display(stdscr, task))
    await process_input(stdscr, cancel_task, cancel_all_tasks, start_tasks)

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()


if __name__ == '__main__':
    asyncio.run(main())
