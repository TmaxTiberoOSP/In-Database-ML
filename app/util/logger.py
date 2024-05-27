# -*- coding: utf-8 -*-
# app/util/logger.py

import logging
from typing import Dict


class Logger(object):
    _loggers: Dict[str, logging.Logger] = {}
    _level: int = logging.WARNING

    def __init__(self):
        raise RuntimeError("Call get_instance() instead")

    @classmethod
    def setLevel(cls, level) -> None:
        cls._level = level
        for logger in cls._loggers.values():
            logger.setLevel(level)

    @classmethod
    def get_instance(cls, name="Common", log="sys.log") -> logging.Logger:
        if cls._loggers.get(name) is None:
            import errno
            import os
            from logging.handlers import RotatingFileHandler

            tb_home = os.environ.get("TB_HOME")
            if tb_home:
                dir_path = f"{tb_home}/instance/opencsd_agent"
            else:
                dir_path = "./"

            try:
                os.makedirs(dir_path)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(dir_path):
                    pass

            logger = logging.getLogger(name)
            logger.setLevel(cls._level)

            fileHandler = RotatingFileHandler(
                filename=f"{dir_path}/{log}",
                maxBytes=100 * 1024 * 1024,
            )
            fileHandler.setFormatter(
                logging.Formatter(
                    "[%(asctime)s.%(msecs)03d] [%(name)10.10s] [%(levelname).1s] %(message)s",
                    datefmt="%m-%dT%H:%M:%S",
                )
            )
            logger.addHandler(fileHandler)

            cls._loggers[name] = logger

        return cls._loggers[name]


class WithLogger(object):
    log: logging.Logger

    def __init__(self, name="", log="") -> None:
        args = [name if name != "" else self.__class__.__name__]

        if log != "":
            args.append(log)

        self.log = Logger.get_instance(*args)
