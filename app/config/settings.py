#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/config/setting.py

from functools import lru_cache

from fastapi import Request
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Python ML Server"
    host: str = "127.0.0.1"
    port: int = 3000

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache()
def get() -> Settings:
    return Settings()


def get_settings(request: Request) -> Settings:
    return request.app.settings
