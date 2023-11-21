#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/loss_fn_model.py

from sqlalchemy import Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.enum.loss_fn_enum import LossFnEnum
from app.model.base_model import BaseEntity


class LossFnEntity(BaseEntity):
    type: LossFnEnum = Column(Enum(LossFnEnum), nullable=False)
    name: str = Column(String, nullable=False)
    params: str = Column(String)
    mid: int = Column(ForeignKey("model.id", ondelete="CASCADE"), nullable=False)

    model = relationship(
        "ModelEntity",
        back_populates="optimizer",
        uselist=False,
    )