# -*- coding: utf-8 -*-
"""
Created on Sat May 16 10:04:05 2015
Initializes logging services.

__author__ = Jorge L. Martinez
"""
from logging import *
from logging.handlers import SysLogHandler


def add_syslog(app_name, address, port=514, level=INFO):
    """
    Adds the option of using a syslog.
    :param app_name:
    :param address: Syslog server address
    :param port: Syslog server port
    :param level:
    :return:
    """
    formatter = Formatter('%(asctime)s ' + app_name + ': <%(levelname)s> %(message)s', datefmt='%b %d %H:%M:%S')

    logger = getLogger()
    handler_syslog = SysLogHandler(address=(address, port))
    handler_syslog.setLevel(level)
    handler_syslog.setFormatter(formatter)

    logger.addHandler(handler_syslog)
    logger.setLevel(DEBUG)


def add_logfile(filename="Log.log", formatter=Formatter('%(asctime)s <%(levelname)s>: %(message)s'), erase=True,
                level=DEBUG):
    """
    Adds the option of using a file output for log
    :param filename:
    :param formatter:
    :param erase:
    :param level:
    :return:
    """

    # Tries to erase the file
    if erase:
        with open(filename, "w"):
            pass

    file_handler = FileHandler(filename, encoding='UTF-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    logger = getLogger()
    logger.setLevel(DEBUG)
    logger.addHandler(file_handler)


def add_console_log(formatter=Formatter('%(asctime)s <%(levelname)s>: %(message)s'), level=DEBUG):
    """
    Adds the option of using a console based log.
    :param formatter:
    :param level:
    :return:
    """
    console_handler = StreamHandler()
    console_handler.setLevel(DEBUG)
    console_handler.setFormatter(formatter)

    logger = getLogger()
    logger.setLevel(DEBUG)
    logger.addHandler(console_handler)
