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
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(query)
        data = cursor.fetchall()
        self.labels = []
        self.image_data = []
        self.transform = transform

        for record in data:
            label, blob_data = record[0], record[1]
            b_stream = blob_data.getBinaryStream()
            img_data = io.BytesIO()

            chunk = b_stream.read()
            while chunk != -1:
                img_data.write(chunk.to_bytes(1, "little"))
                chunk = b_stream.read()

            image = Image.open(img_data)

            if self.transform is not None:
                image = self.transform(image)

            label = torch.tensor(label, dtype=torch.long)
            image_data = torch.tensor(np.array(image), dtype=torch.float32)

            self.labels.append(label)
            self.image_data.append(image_data)

        cursor.close()
        conn.close()

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        label = self.labels[idx]
        image_data = self.image_data[idx]
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
