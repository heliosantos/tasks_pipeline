import logging



'''
logging:
  enabled: true
  console: true
  file: tasks_pipeline.log
  loggers:
    - tasks_pipeline:
        level: DEBUG

'''


def setup_loggers(loggersConfig):
    if not loggersConfig.get('enabled', True):
        return

    defaultUseConsole = loggersConfig.get('console', False)
    defaultFile = loggersConfig.get('file')

    for loggerName, loggerConfig in loggersConfig.get('loggers', {}).items():
        level = loggerConfig.get('level', 'INFO')
        level = logging.getLevelName(level)
        useConsole = loggerConfig.get('console', defaultUseConsole)
        file = loggerConfig.get('file', defaultFile)

        logger = logging.getLogger(loggerName)
        logger.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
