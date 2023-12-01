#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/config/tibero.py

import jaydebeapi
from fastapi import Depends

from .settings import get

settings = get()


def get_db_connection(
    db_host: str = settings.db_host,
    db_port: int = settings.db_port,
    db_name: str = settings.db_name,
    db_user: str = settings.db_user,
    db_passwd: str = settings.db_passwd,
    jdbc_driver: str = settings.jdbc_driver,
) -> jaydebeapi.Connection:
    return jaydebeapi.connect(
        "com.tmax.tibero.jdbc.TbDriver",
        f"jdbc:tibero:thin:@{db_host}:{db_port}:{db_name}",
        [db_user, db_passwd],
        jdbc_driver,
    )


async def get_db(conn: jaydebeapi.Connection = Depends(get_db_connection)):
    try:
        yield conn
    finally:
        conn.close()
