#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/loss_fn_model.py

from sqlalchemy import Column, Enum, String

from app.enum.loss_fn_enum import LossFnEnum
from app.model.base_model import BaseEntity


class LossFnEntity(BaseEntity):
    type: LossFnEnum = Column(Enum(LossFnEnum), nullable=False)
    name: str = Column(String, nullable=False)
    params: str = Column(String)