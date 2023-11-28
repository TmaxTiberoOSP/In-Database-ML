#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/routes/model_router.py

from fastapi import APIRouter

from app.model.model import RequestInference, RequestScore, RequestTrain

router = APIRouter(prefix="/models", tags=["Model"])


@router.post("/{model_id}/train")
def train_model(model_id: int, req: RequestTrain):
    pass


@router.post("/{model_id}/inference")
def inference_model(model_id: int, req: RequestInference):
    pass


@router.post("/{model_id}/score")
def score_model(model_id: int, req: RequestScore):
    pass
