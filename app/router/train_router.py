#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/routes/train_router.py

import os

from fastapi import APIRouter, Depends, HTTPException
from jaydebeapi import Connection

from app.config.kernel import KernelClient, get_client
from app.config.tibero import get_db
from app.model.train import (
    RequestTable,
    TrainLogView,
    TrainView,
    get_train_by_id,
    get_train_log_by_id,
)
from app.util.source_generator import get_test_metrics_source

router = APIRouter(prefix="/train", tags=["Train"])


@router.get("/{train_id}", response_model=TrainView)
def get_train_info(
    train_id: int,
    db: Connection = Depends(get_db),
):
    train = get_train_by_id(train_id, db)

    return TrainView(**train.model_dump())


@router.post("/{train_id}/test-metrics")
async def test_metrics_trained_model(
    train_id: int,
    req: RequestTable,
    to_json: bool = False,
    db: Connection = Depends(get_db),
    kc: KernelClient = Depends(get_client),
):
    train = get_train_by_id(train_id, db)

    kernel = await kc.create_kernel()
    if not kernel:
        raise HTTPException(status_code=503, detail="no providers available")

    model_filename = os.path.split(train.path)[1]
    await kernel.send_file(train.path, model_filename)

    result = await kernel.execute(
        get_test_metrics_source(
            model_filename,
            req.table_name,
            req.label_column_name,
            req.data_column_name,
        ),
        "Test model",
    )

    await kernel.stop()

    try:
        result = result[result.index("__RESULT__") + 1 :]
        if to_json:
            return result
        else:
            return "\n".join(result)
    except:
        raise HTTPException(status_code=400)


@router.get("/{train_id}/log", response_model=list[TrainLogView])
def get_train_log(
    train_id: int,
    db: Connection = Depends(get_db),
):
    return [
        TrainLogView(**log.model_dump()) for log in get_train_log_by_id(train_id, db)
    ]
