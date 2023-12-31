#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/routes/model_router.py

from io import StringIO

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from jaydebeapi import Connection

from app.config.kernel import KernelClient, KernelConnection, get_client
from app.config.tibero import get_db
from app.model.model import Model, get_model_from_db
from app.model.train import RequestTrain, Train, new_train
from app.util.source_generator import (
    get_dataloader_source,
    get_network_source,
    get_train_source,
)

router = APIRouter(prefix="/models", tags=["Model"])


@router.get("/{model_id}", response_model=Model)
def get_model(model_id: int, db: Connection = Depends(get_db)):
    return get_model_from_db(model_id, db)


async def train_task(
    req: RequestTrain, model: Model, train: Train, kernel: KernelConnection
):
    await kernel.execute(f"_SERVER.train_id = {train.id}", "Step 1: Set train id")
    await kernel.execute(
        get_dataloader_source(
            req.dataset.table_name,
            req.dataset.label_column_name,
            req.dataset.data_column_name,
            req.testset.table_name,
            req.testset.label_column_name,
            req.testset.data_column_name,
        ),
        "Step 2: Ready dataloader",
    )
    await kernel.execute(
        get_network_source(model),
        "Step 3: Define network",
    )
    await kernel.execute(
        get_train_source(model, train.id, req.num_epochs, req.mini_batches),
        "Step 4: Train model",
    )
    await kernel.stop()


@router.post("/{model_id}/train", response_class=PlainTextResponse)
async def train_model(
    model_id: int,
    req: RequestTrain,
    background_tasks: BackgroundTasks,
    db: Connection = Depends(get_db),
    kc: KernelClient = Depends(get_client),
):
    model = get_model_from_db(model_id, db)
    kernel = await kc.create_kernel()
    if not kernel:
        raise HTTPException(status_code=503, detail="no providers available")
    train = new_train(model_id, db)

    background_tasks.add_task(train_task, req, model, train, kernel)

    return str(train.id)


def generate_source_response(source: str, filename: str) -> StreamingResponse:
    vfile = StringIO()

    vfile.write(source)

    return StreamingResponse(
        iter([vfile.getvalue()]),
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )


@router.get("/{model_id}/source/dataloader")
async def generate_dataloader_source(
    model_id: int,
    dataset_table: str,
    dataset_label: str,
    dataset_data: str,
    testset_table: str,
    testset_label: str,
    testset_data: str,
    db: Connection = Depends(get_db),
):
    model = get_model_from_db(model_id, db)

    return generate_source_response(
        get_dataloader_source(
            dataset_table,
            dataset_label,
            dataset_data,
            testset_table,
            testset_label,
            testset_data,
        ),
        f"{model.id}_{model.name}_dataloader_source.py",
    )


@router.get("/{model_id}/source/network")
async def generate_network_source(model_id: int, db: Connection = Depends(get_db)):
    model = get_model_from_db(model_id, db)

    return generate_source_response(
        get_network_source(model), f"{model.id}_{model.name}_network_source.py"
    )


@router.get("/{model_id}/source/train")
async def generate_train_source(
    model_id: int,
    train_id: int,
    num_epochs: int,
    mini_batches: int,
    db: Connection = Depends(get_db),
):
    model = get_model_from_db(model_id, db)

    return generate_source_response(
        get_train_source(model, train_id, num_epochs, mini_batches),
        f"{model.id}_{model.name}_train_source.py",
    )
