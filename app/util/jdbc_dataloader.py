#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/util/jdbc_dataloader.py

import io
from typing import Callable

import jaydebeapi
import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

get_db_connection: Callable[[], jaydebeapi.Connection]
try:
    get_db_connection
except NameError:

    def get_db_connection() -> jaydebeapi.Connection:
        return jaydebeapi.connect(
            "com.tmax.tibero.jdbc.TbDriver",
            f"jdbc:tibero:thin:@127.0.0.1:8629:tibero",
            ["tibero", "tmax"],
            "$TB_HOME/client/lib/jar/tibero7-jdbc.jar",
        )


class Classification_Dataset(Dataset):
    def __init__(self, query, transform=None):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        self.query = query
        self.cursor.execute(self.query)
        self.data = self.cursor.fetchall()
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        record = self.data[idx]
        label, binary_data = record[0], record[1]

        # binary data to PIL image
        image = Image.open(io.BytesIO(binary_data))

        # preprocessing if necessary
        if self.transform is not None:
            image = self.transform(image)

        label = torch.tensor(label, dtype=torch.int)
        image_data = torch.tensor(np.array(image), dtype=torch.float32).permute(2, 0, 1)

        return image_data, label


# preprocessing 예시(차후 proprecssing.py로 뺄 내용)
norm_transform = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ]
)

train_loader = DataLoader(
    Classification_Dataset(
        "SELECT {dataset.label_column_name}, {dataset.data_column_name} FROM {dataset.table_name}",
        norm_transform,
    ),
    batch_size=10,
    shuffle=True,
    num_workers=4,
)

test_loader = DataLoader(
    Classification_Dataset(
        "SELECT {testset.label_column_name}, {testset.data_column_name} FROM {testset.table_name}",
        norm_transform,
    ),
    batch_size=10,
    shuffle=False,
    num_workers=4,
)
