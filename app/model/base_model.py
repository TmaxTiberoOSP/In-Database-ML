#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/model/base_model.py

import re
from abc import ABC
from datetime import datetime
from typing import Union

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class BaseEntity:
    __table_args__ = {"sqlite_autoincrement": True}

    id: Union[int, Column] = Column(Integer, primary_key=True)
    created_at: Union[datetime, Column] = Column(DateTime, default=datetime.now)
    updated_at: Union[datetime, Column] = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    @declared_attr
    def __tablename__(cls) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower().replace("_entity", "")


class Base(BaseModel, ABC):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
