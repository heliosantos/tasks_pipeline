import logging
import datetime


def setup_loggers(loggersConfig):
    if not loggersConfig or not loggersConfig.get("enabled", True):
        return

    defaultUseConsole = loggersConfig.get("console", False)
    defaultFile = loggersConfig.get("file")
    defaultFile = datetime.datetime.now().strftime(defaultFile)

    for loggerName, loggerConfig in loggersConfig.get("loggers", {}).items():
        level = loggerConfig.get("level", "INFO")
        level = logging.getLevelName(level)
        useConsole = loggerConfig.get("console", defaultUseConsole)
        file = loggerConfig.get("file", defaultFile)
        file = datetime.datetime.now().strftime(file)

        logger = logging.getLogger(loggerName)
        logger.setLevel(level)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        if file:
            fh = logging.FileHandler(file)
            fh.setLevel(level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        if useConsole:
            ch = logging.StreamHandler()
            ch.setLevel(level)
            ch.setFormatter(formatter)
            logger.addHandler(ch)
