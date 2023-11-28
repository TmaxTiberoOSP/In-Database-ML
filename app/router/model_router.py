#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/routes/model_router.py

from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from jaydebeapi import Connection

from app.config.tibero import get_db
from app.model.model import (
    Model,
    RequestInference,
    RequestScore,
    RequestTrain,
    get_model_from_db,
)
from app.util.source_generator import get_network_source, get_train_source

router = APIRouter(prefix="/models", tags=["Model"])


@router.get("/{model_id}", response_model=Model)
def get_model(model_id: int, db: Connection = Depends(get_db)):
    return get_model_from_db(model_id, db)


@router.post("/{model_id}/train")
def train_model(model_id: int, req: RequestTrain):
    pass


@router.post("/{model_id}/inference")
def inference_model(model_id: int, req: RequestInference):
    pass


@router.post("/{model_id}/score")
def score_model(model_id: int, req: RequestScore):
    pass


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


@router.get("/{model_id}/source/network")
async def generate_network_source(model_id: int, db: Connection = Depends(get_db)):
    model = get_model_from_db(model_id, db)

    return generate_source_response(
        get_network_source(model), f"{model.id}_{model.name}_network_source.py"
    )


@router.get("/{model_id}/source/train")
async def generate_train_source(
    model_id: int, num_epochs: int, mini_batches: int, db: Connection = Depends(get_db)
):
    model = get_model_from_db(model_id, db)

    return generate_source_response(
        get_train_source(model, num_epochs, mini_batches),
        f"{model.id}_{model.name}_train_source.py",
    )
