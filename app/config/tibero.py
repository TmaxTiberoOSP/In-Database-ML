#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/config/tibero.py

import jaydebeapi
from fastapi import Depends

from .settings import get

settings = get()


def get_db_connection() -> jaydebeapi.Connection:
    return jaydebeapi.connect(
        "com.tmax.tibero.jdbc.TbDriver",
        f"jdbc:tibero:thin:@{settings.db_host}:{settings.db_port}:{settings.db_name}",
        [settings.db_user, settings.db_passwd],
        settings.jdbc_driver,
    )


async def get_db(conn: jaydebeapi.Connection = Depends(get_db_connection)):
    try:
        yield conn
    finally:
        conn.close()
