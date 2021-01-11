# coding: utf-8

import functools
import logging
import sys
import time
from pathlib import Path

from termcolor import colored

# sentry.io
# from utils import EventHandler

# specify setting for different logging levels
LOG_FORMATTER = {
    logging.ERROR: ["red", "".rjust(4), ["reverse"]],
    logging.WARNING: ["yellow", "".rjust(2), ["underline"]],
    logging.DEBUG: ["white", "".rjust(4), ["blink"]],
    logging.INFO: ["green", "".rjust(5), ["blink"]],
    logging.CRITICAL: ["magenta", "".rjust(1), ["blink"]],
}


class ColorfulFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super(ColorfulFormatter, self).__init__(*args, **kwargs)

    def formatMessage(self, record):
        msg = super(ColorfulFormatter, self).formatMessage(record)
        if record.levelno in LOG_FORMATTER:
            new_msg = "{prefix}{space}{msg}".format(
                prefix=colored(
                    text=record.levelname,
                    color=LOG_FORMATTER[record.levelno][0],
                    attrs=LOG_FORMATTER[record.levelno][2],
                ),
                space=LOG_FORMATTER[record.levelno][1],
                msg=msg,
            )
            return new_msg


class ListFilter(logging.Filter):
    """
    # https://stackoverflow.com/questions/22934616/multi-line-logging-in-python
    The other optional keyword argument is extra which can be used to pass a dictionary
    which is used to populate the __dict__ of the LogRecord created for the logging event with user-defined attributes.
    """

    def filter(self, record):
        if hasattr(record, "list"):
            for v in record.list:
                record.msg += f"\n\t\t  {v}"
        # extra = {'dict': Dict}
        # 用 count 记数，增加序号，用于检查番号提取（特定需求）
        if hasattr(record, "dict"):
            count = 1
            for k, v in record.dict.items():
                record.msg += f"\n\t\t  No.{count:<2d} file: {str(k)} -> id: {v} "
                count += 1
        return super(ListFilter, self).filter(record)


# so that calling setup_logger multiple times won't add many handlers
@functools.lru_cache()
def setup_logger(name="cap", debug=False):
    """
    指定保存日志的文件路径，日志级别，以及调用文件
    日志等级 debug 只写入log文件，其他都会在控制台打印
    只有控制台输出有颜色
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    ch = logging.StreamHandler(stream=sys.stdout)
    # for debug
    if debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    # 控制台输出使用 ColorFormatter
    formatter = ColorfulFormatter(
        "[%(asctime)s %(name)s]: " + colored("%(message)s", "cyan"),
        datefmt="%m/%d",
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    # ---------------创建一个handler，用于写入日志文件
    log_time = time.strftime("%m-%d", time.localtime(time.time()))
    filename = Path(__file__).parent.parent.joinpath(f"{log_time}.log")
    fh = logging.StreamHandler(_cached_log_stream(filename))

    fh_formatter = logging.Formatter(
        "[%(asctime)s] %(name)s %(levelname) 8s: %(message)s", datefmt="%m/%d %H:%M:%S"
    )
    fh.setFormatter(fh_formatter)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    # only for test
    # 按行打印 list 或者 dict
    logger.addFilter(ListFilter())

    return logger


# cache the opened file object, so that different calls to `setup_logger`
# with the same file name can safely write to the same file.
@functools.lru_cache(maxsize=None)
def _cached_log_stream(filename):
    return Path.open(filename, "a")


if __name__ == "__main__":
    log = setup_logger()

    d = {"list": ["str1", "str2", "str3"]}
    # # d = {'dict': {'one': 'test_one', 'two': 'test_two'}}
    log.info("This shows extra", extra=d)
    log.info("this is info")
    log.error("this is error")
    log.warning("this is warning")
    log.critical("this is critical")
