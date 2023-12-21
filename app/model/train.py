#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/train.py

import io
from datetime import datetime

import torchvision.transforms as transforms
from fastapi import HTTPException
from jaydebeapi import Connection
from PIL import Image
from pydantic import BaseModel, ConfigDict
from torch import Tensor


class RequestTable(BaseModel):
    table_name: str
    label_column_name: str
    data_column_name: str


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
    path: str | None

    def __init__(self, id, mid, kernel, status, path) -> None:
        super().__init__(id=id, mid=mid, kernel=kernel, status=status, path=path)


class TrainView(BaseModel):
    train_id: int
    model_id: int
    kernel: str
    status: str
    path: str

    model_config = ConfigDict(protected_namespaces=())

    def __init__(self, id: int, mid: int, kernel: str, status: str, path: str) -> None:
        super().__init__(
            train_id=id,
            model_id=mid,
            kernel=kernel,
            status=status.strip(),
            path=path if path else "",
        )


def new_train(mode_id: int, db: Connection) -> Train:
    status = "request train"
    try:
        cursor = db.cursor()

        cursor.execute(f"SELECT sys.SEQ_ML_TRAIN.NEXTVAL FROM DUAL")
        (train_id,) = cursor.fetchone()

        cursor.execute(
            "INSERT INTO sys.ML_TRAIN (ID, MID, STATUS) VALUES "
            f"({train_id}, {mode_id}, '{status}');"
        )

        cursor.execute(f"SELECT * FROM sys.ML_TRAIN WHERE ID = {train_id}")
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

        cursor.execute(f"SELECT * FROM sys.ML_TRAIN WHERE ID = {id}")
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="train info not found")

        return Train(*result)
    finally:
        cursor.close()


class RequestInferenceImage(BaseModel):
    data_id: int
    # TODO: 모델 정보를 바탕으로 width, height 추출하는 방법 리서치
    width: int = 32
    height: int = 32


def get_inference_image_from_db(req: RequestInferenceImage, db: Connection) -> Tensor:
    try:
        cursor = db.cursor()

        cursor.execute(f"SELECT DATA FROM sys.ML_INFERENCE WHERE ID={req.data_id}")
        result = cursor.fetchone()

        if not result:
            raise HTTPException(
                status_code=404, detail="inference input data not found"
            )

        (blob,) = result
        image = Image.open(io.BytesIO(bytes(blob.getBytes(1, int(blob.length())))))
        transform = transforms.Compose(
            [transforms.Resize((req.width, req.height)), transforms.ToTensor()]
        )

        return transform(image).unsqueeze(0)
    finally:
        cursor.close()


class TrainLog(BaseModel):
    tid: int
    log: str
    create_at: datetime

    def __init__(self, tid, log, create_at) -> None:
        super().__init__(tid=tid, log=log, create_at=create_at)


class TrainLogView(BaseModel):
    log: str
    create_at: datetime


def get_train_log_by_id(train_id: int, db: Connection) -> list[TrainLog]:
    try:
        cursor = db.cursor()

        cursor.execute(
            f"SELECT * FROM sys.ML_TRAIN_LOG WHERE TID = {train_id} ORDER BY CREATEDAT"
        )
        result = cursor.fetchall()

        if not result:
            raise HTTPException(status_code=404, detail="train info not found")

        result = [TrainLog(*row) for row in result]

        return result
    finally:
        cursor.close()
