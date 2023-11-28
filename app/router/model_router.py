#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/routes/model_router.py

from fastapi import APIRouter, Depends
from jaydebeapi import Connection

from app.config.tibero import get_db
from app.model.model import (
    Model,
    RequestInference,
    RequestScore,
    RequestTrain,
    get_model_from_db,
)

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
