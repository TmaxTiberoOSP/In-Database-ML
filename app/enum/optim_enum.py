#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/enum/optim_enum.py

from enum import auto, unique

from app.enum import AutoNameEnum


@unique
class OptimEnum(AutoNameEnum):
    Adadelta = auto()
    Adagrad = auto()
    Adam = auto()
    AdamW = auto()
    SparseAdam = auto()
    Adamax = auto()
    ASGD = auto()
    LBFGS = auto()
    NAdam = auto()
    RAdam = auto()
    RMSprop = auto()
    Rprop = auto()
    SGD = auto()
