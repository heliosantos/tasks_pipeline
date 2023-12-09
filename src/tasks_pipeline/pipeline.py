import asyncio
import curses
import sys

from .tasks_logger import setup_loggers
from .view import display
from .controller import process_input
from .pipeline_model import PipelineModel
from .config import load_config


async def main(stdscr):
    if len(sys.argv) < 2:
        print('usage: tasks_pipeline configFile')
        return

    curses.start_color()
    curses.use_default_colors()
    curses.curs_set(0)

    config = load_config(sys.argv[1])

    setup_loggers(config.get('logging'))

    pipelineModel = PipelineModel(config)

    asyncio.create_task(display(stdscr, pipelineModel))
    await process_input(stdscr, pipelineModel)

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
