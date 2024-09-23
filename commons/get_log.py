import logging
import os
from logging.handlers import RotatingFileHandler

from commons.setting import FILE_PATH
import time

log_path = FILE_PATH['log']
print(log_path)
if not os.path.exists(log_path):
    os.mkdir(log_path)

logfile_name = log_path + r'\test.{}.log'.format(time.strftime('%Y%m%d'))


class Handlelogs:
    @classmethod
    def output_logs(cls):
        logger = logging.getLogger(__name__)

        if not logger.handlers:
            logger.setLevel(logging.DEBUG)
            log_format = logging.Formatter(
                '%(levelname)s - %(asctime)s - %(filename)s:%(lineno)d - [%(module)s:%(funcName)s] - %(message)s '
            )
            sh = logging.StreamHandler()
            sh.setLevel(logging.DEBUG)
            sh.setFormatter(log_format)
            logger.addHandler(sh)

            fh = RotatingFileHandler(filename=logfile_name, mode='a', maxBytes=5242880, backupCount=7, encoding='utf-8')
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(log_format)
            logger.addHandler(fh)
        return logger
handle = Handlelogs()
logs = handle.output_logs()

logs.info("info")