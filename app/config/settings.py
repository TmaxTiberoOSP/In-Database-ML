#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/config/settings.py

from functools import lru_cache
from pathlib import Path
from typing import TypedDict

from fastapi import Request
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJ_PATH = str(Path(__file__).parent.parent.parent.absolute())


class DBInfo(TypedDict):
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_passwd: str


class Settings(BaseSettings):
    app_name: str = "Python ML Server"
    # Server
    host: str = "127.0.0.1"
    port: int = 3000

    # DB
    jdbc_driver: str = "$TB_HOME/client/lib/jar/tibero7-jdbc.jar"
    db_host: str = "127.0.0.1"
    db_port: int = "8629"
    db_name: str = "tibero"
    db_user: str = "tibero"
    db_passwd: str = "tmax"
    meta_db_url: str = f"sqlite:///{PROJ_PATH}/ml.db"

    # Kernel
    kernel_master_host: str = "127.0.0.1"
    kernel_master_port: int = 8090
    kernel_root: str = f"{PROJ_PATH}/kernel_root"

    model_config = SettingsConfigDict(env_file=".env")

    def get_db_info(self) -> DBInfo:
        return {
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "db_user": self.db_user,
            "db_passwd": self.db_passwd,
        }


@lru_cache()
def get() -> Settings:
    return Settings()


def get_settings(request: Request) -> Settings:
    return request.app.settings
