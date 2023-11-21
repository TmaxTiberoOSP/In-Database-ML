#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/layer_model.py

from sqlalchemy import Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.enum.nn_enum import NNEnum
from app.model.base_model import BaseEntity


class LayerEntity(BaseEntity):
    type: NNEnum = Column(Enum(NNEnum), nullable=False)
    name: str = Column(String, nullable=False)
    params: str = Column(String)
    mid: int = Column(ForeignKey("model.id", ondelete="CASCADE"), nullable=False)

    model = relationship(
        "ModelEntity",
        back_populates="containers",
        uselist=False,
    )