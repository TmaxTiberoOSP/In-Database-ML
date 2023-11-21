#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/model_model.py

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.model.base_model import BaseEntity


class ModelEntity(BaseEntity):
    name: str = Column(String, nullable=False)
    desc: str = Column(String)

    layers = relationship(
        "LayerEntity", back_populates="model", cascade="all, delete-orphan"
    )
    loss_fn = relationship(
        "LossFnEntity",
        back_populates="model",
        cascade="all, delete-orphan",
        uselist=False,
    )
    optimizer = relationship(
        "OptimizerEntity",
        back_populates="model",
        cascade="all, delete-orphan",
        uselist=False,
    )