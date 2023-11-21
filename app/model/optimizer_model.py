#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/optimizer_model.py

from sqlalchemy import Column, Enum, String

from app.enum.optim_enum import OptimEnum
from app.model.base_model import BaseEntity


class OptimizerEntity(BaseEntity):
    type: OptimEnum = Column(Enum(OptimEnum), nullable=False)
    name: str = Column(String, nullable=False)
    params: str = Column(String)