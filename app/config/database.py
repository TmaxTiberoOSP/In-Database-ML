#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/config/database.py

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.model.base_model import BaseEntity

from .settings import get

engine = create_engine(
    get().meta_db_url, connect_args={"check_same_thread": False}, echo=False
)
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init():
    BaseEntity.metadata.create_all(engine)
    event.listen(engine, "connect", lambda c, _: c.execute("pragma foreign_keys=on"))


def get_session():
    try:
        session = SessionFactory()
        yield session
    finally:
        session.close()
