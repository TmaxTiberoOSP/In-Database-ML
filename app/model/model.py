#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/model.py

from pydantic import BaseModel


class RequestTable(BaseModel):
    table_name: str
    label_column_name: str
    data_column_name: str


class RequestTrain(BaseModel):
    train_id: int
    dataset: RequestTable
    testset: RequestTable


class RequestInference(BaseModel):
    train_id: int
    img_id: int


class RequestScore(BaseModel):
    train_id: int
    testset: RequestTable
