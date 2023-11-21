#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/container_model.py

from sqlalchemy import Column, Enum, String

from app.enum.nn_enum import NNEnum
from app.model.base_model import BaseEntity


class ContainerEntity(BaseEntity):
    type: NNEnum = Column(Enum(NNEnum), nullable=False)
    name: str = Column(String, nullable=False)
    params: str = Column(String)