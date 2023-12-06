#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/routes/train_router.py

from fastapi import APIRouter, Depends
from jaydebeapi import Connection

from app.config.tibero import get_db
from app.model.train import TrainLogView, get_train_log_by_id

router = APIRouter(prefix="/train", tags=["Train"])


@router.post("/{train_id}/log", response_model=list[TrainLogView])
def get_train_log(
    train_id: int,
    db: Connection = Depends(get_db),
):
    return [
        TrainLogView(**log.model_dump()) for log in get_train_log_by_id(train_id, db)
    ]
