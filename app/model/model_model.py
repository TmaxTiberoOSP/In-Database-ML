#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/model_model.py

from sqlalchemy import Column, String

from app.model.base_model import BaseEntity


class ModelEntity(BaseEntity):
    name: str = Column(String, nullable=False)
    desc: str = Column(String)