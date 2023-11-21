#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/config/settings.py

from functools import lru_cache
from pathlib import Path

from fastapi import Request
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJ_PATH = str(Path(__file__).parent.parent.parent.absolute())


class Settings(BaseSettings):
    app_name: str = "Python ML Server"
    host: str = "127.0.0.1"
    port: int = 3000
    meta_db_url: str = f"sqlite:///{PROJ_PATH}/ml.db"

    # Kernel
    kernel_master_host: str = "127.0.0.1"
    kernel_master_port: int = 8090
    kernel_root: str = f"{PROJ_PATH}/kernel_root"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache()
def get() -> Settings:
    return Settings()


def get_settings(request: Request) -> Settings:
    return request.app.settings
