import logging

LOG_LEVEL = logging.INFO
LOG_FILE = 'scrader.log'
LOG_FORMAT = '%(asctime)s %(levelname)-8s %(filename)s:%(lineno)-4d: %(message)s'
LOG_DATE_FORMAT = '%H:%M:%S'
log_formatter = logging.Formatter(LOG_FORMAT)
root_logger = logging.getLogger('scrader')
root_logger.setLevel(LOG_LEVEL)
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(log_formatter)
root_logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
root_logger.addHandler(console_handler)
global LOG
LOG = root_logger
LOG.info('Logger initialized')
