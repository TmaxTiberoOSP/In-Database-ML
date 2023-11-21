#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/enum/__init__.py

from enum import auto, unique

from app.enum import AutoNameEnum


@unique
class NNEnum(AutoNameEnum):
    # Containers
    Module = auto()
    Sequential = auto()
    ModuleList = auto()
    ModuleDict = auto()
    ParameterList = auto()

    # Convolution Layers
    Conv1d = auto()
    Conv2d = auto()
    Conv3d = auto()
    ConvTranspose1d = auto()
    ConvTranspose2d = auto()
    ConvTranspose3d = auto()
    LazyConv1d = auto()
    LazyConv2d = auto()
    LazyConv3d = auto()
    LazyConvTranspose1d = auto()
    LazyConvTranspose2d = auto()
    LazyConvTranspose3d = auto()
    Unfold = auto()
    Fold = auto()

    # Pooling layers
    MaxPool1d = auto()
    MaxPool2d = auto()
    MaxPool3d = auto()
    MaxUnpool1d = auto()
    MaxUnpool2d = auto()
    MaxUnpool3d = auto()
    AvgPool1d = auto()
    AvgPool2d = auto()
    AvgPool3d = auto()
    FractionalMaxPool2d = auto()
    FractionalMaxPool3d = auto()
    LPPool1d = auto()
    LPPool2d = auto()
    AdaptiveMaxPool1d = auto()
    AdaptiveMaxPool2d = auto()
    AdaptiveMaxPool3d = auto()
    AdaptiveAvgPool1d = auto()
    AdaptiveAvgPool2d = auto()
    AdaptiveAvgPool3d = auto()

    # Padding Layers
    ReflectionPad1d = auto()
    ReflectionPad2d = auto()
    ReflectionPad3d = auto()
    ReplicationPad1d = auto()
    ReplicationPad2d = auto()
    ReplicationPad3d = auto()
    ZeroPad2d = auto()
    ConstantPad1d = auto()
    ConstantPad2d = auto()
    ConstantPad3d = auto()

    # Non-linear Activations (weighted sum, nonlinearity)
    ELU = auto()
    Hardshrink = auto()
    Hardsigmoid = auto()
    Hardtanh = auto()
    Hardswish = auto()
    LeakyReLU = auto()
    LogSigmoid = auto()
    MultiheadAttention = auto()
    PReLU = auto()
    ReLU = auto()
    ReLU6 = auto()
    RReLU = auto()
    SELU = auto()
    CELU = auto()
    GELU = auto()
    Sigmoid = auto()
    SiLU = auto()
    Mish = auto()
    Softplus = auto()
    Softshrink = auto()
    Softsign = auto()
    Tanh = auto()
    Tanhshrink = auto()
    Threshold = auto()
    GLU = auto()

    # Non-linear Activations (other)
    Softmin = auto()
    Softmax = auto()
    Softmax2d = auto()
    LogSoftmax = auto()
    AdaptiveLogSoftmaxWithLoss = auto()

    # Normalization Layers
    BatchNorm1d = auto()
    BatchNorm2d = auto()
    BatchNorm3d = auto()
    LazyBatchNorm1d = auto()
    LazyBatchNorm2d = auto()
    LazyBatchNorm3d = auto()
    GroupNorm = auto()
    SyncBatchNorm = auto()
    InstanceNorm1d = auto()
    InstanceNorm2d = auto()
    InstanceNorm3d = auto()
    LazyInstanceNorm1d = auto()
    LazyInstanceNorm2d = auto()
    LazyInstanceNorm3d = auto()
    LayerNorm = auto()
    LocalResponseNorm = auto()

    # Recurrent Layers
    RNNBase = auto()
    RNN = auto()
    LSTM = auto()
    GRU = auto()
    RNNCell = auto()
    LSTMCell = auto()
    GRUCell = auto()

    # Transformer Layers
    Transformer = auto()
    TransformerEncoder = auto()
    TransformerDecoder = auto()
    TransformerEncoderLayer = auto()
    TransformerDecoderLayer = auto()

    # Linear Layers
    Identity = auto()
    Linear = auto()
    Bilinear = auto()
    LazyLinear = auto()

    # Dropout Layers
    Dropout = auto()
    Dropout1d = auto()
    Dropout2d = auto()
    Dropout3d = auto()
    AlphaDropout = auto()
    FeatureAlphaDropout = auto()

    # Sparse Layers
    Embedding = auto()
    EmbeddingBag = auto()

    # Distance Functions
    CosineSimilarity = auto()
    PairwiseDistance = auto()

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

    # Vision Layers
    PixelShuffle = auto()
    PixelUnshuffle = auto()
    Upsample = auto()
    UpsamplingNearest2d = auto()
    UpsamplingBilinear2d = auto()

    # Shuffle Layers
    ChannelShuffle = auto()

    # DataParallel Layers (multi-GPU, distributed)
    DataParallel = auto()
    parallel_DistributedDataParallel = auto()
