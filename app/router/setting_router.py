#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/routes/setting_router.py

from fastapi import APIRouter, Depends
from jaydebeapi import Connection

from app.config.tibero import get_db
from app.util import sql_reader, static_dir

router = APIRouter(prefix="/setting", tags=["Setting"])


@router.post("/init-db")
def init_db(
    reset: bool = False,
    db: Connection = Depends(get_db),
):
    cursor = db.cursor()

    if reset:
        with open(f"{static_dir}/drop_table.sql", "r") as file:
            for sql in sql_reader(file):
                cursor.execute(sql)

    with open(f"{static_dir}/create_table.sql", "r") as file:
        for sql in sql_reader(file):
            cursor.execute(sql)

    db.commit()
    cursor.close()
