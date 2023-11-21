#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/enum/loss_fn_enum.py

from enum import auto, unique

from app.enum import AutoNameEnum


@unique
class LossFnEnum(AutoNameEnum):
    # Loss Functions
    L1Loss = auto()
    MSELoss = auto()
    CrossEntropyLoss = auto()
    CTCLoss = auto()
    NLLLoss = auto()
    PoissonNLLLoss = auto()
    GaussianNLLLoss = auto()
    KLDivLoss = auto()
    BCELoss = auto()
    BCEWithLogitsLoss = auto()
    MarginRankingLoss = auto()
    HingeEmbeddingLoss = auto()
    MultiLabelMarginLoss = auto()
    HuberLoss = auto()
    SmoothL1Loss = auto()
    SoftMarginLoss = auto()
    MultiLabelSoftMarginLoss = auto()
    CosineEmbeddingLoss = auto()
    MultiMarginLoss = auto()
    TripletMarginLoss = auto()
    TripletMarginWithDistanceLoss = auto()
