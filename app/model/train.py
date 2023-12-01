#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/train.py

from fastapi import HTTPException
from jaydebeapi import Connection
from pydantic import BaseModel

from app.model import RequestTable


class RequestTrain(BaseModel):
    num_epochs: int
    mini_batches: int
    dataset: RequestTable
    testset: RequestTable


class Train(BaseModel):
    id: int
    mid: int
    kernel: str
    status: str
    path: str

    def __init__(self, id, mid, kernel, status, path) -> None:
        super().__init__(id=id, mid=mid, kernel=kernel, status=status, path=path)


def new_train(mode_id: int, db: Connection) -> Train:
    status = "request train"
    try:
        cursor = db.cursor()

        cursor.execute(f"SELECT SEQ_ML_TRAIN.NEXTVAL FROM DUAL")
        (train_id,) = cursor.fetchone()

        cursor.execute(
            "INSERT INTO ML_TRAIN (ID, MID, STATUS) VALUES "
            f"({train_id}, {mode_id}, '{status}');"
        )

        cursor.execute(f"SELECT * FROM ML_TRAIN WHERE ID = {train_id}")
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="train generate fail")

        db.commit()

        return Train(train_id, mode_id, "", status, "")
    finally:
        cursor.close()


def get_train_by_id(id: int, db: Connection) -> Train:
    try:
        cursor = db.cursor()

        cursor.execute(f"SELECT * FROM ML_TRAIN WHERE ID = {id}")
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="train info not found")

        return Train(*result)
    finally:
        cursor.close()
