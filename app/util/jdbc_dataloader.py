#!/usr/bin/env python
# -*- coding: utf-8 -*-
# utils/loader.py

import torch
from torch.utils.data import Dataset, Dataloader
import jaydebeapi
from PIL import Image
import io
from torchvision import transforms
import numpy as np

"""
#database information(To fix on your setting)
tbdriver = "com.tmax.tibero.jdbc.TbDriver"
database_url = "jdbc:tibero:thin:@<hostname>:<port>:<database_name>"
username = "<your_username>"
password = "<your_password>"
jdbc_driver_jar = "/path/to/tibero7-jdbc.jar"  # Path to the Tibero JDBC driver JAR file
"""

tbdriver = "com.tmax.tibero.jdbc.TbDriver"
database_url = "jdbc:tibero:thin:@jamong-dock:9440:TAC"
username = "sys"
password = "tibero"
jdbc_driver_jar = "$TB_HOME/client/lib/jar/tibero7-jdbc.jar"  # Path to the Tibero JDBC driver JAR file



class Classification_Dataset(Dataset):
    def __init__(self, train: bool = True, jdbc_connection, query, transform = None):
        self.conn = jdbc_connection
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


        #binary data to PIL image
        image = Image.open(io.BytesIO(binary_data))

        #preprocessing if necessary
        if self.transform is not None:
            image= = self.transform(image)

        label = torch.tensor(label, dtype = torch.int)
        image_data = torch.tensor(np.array(image), dtype=torch.float32).permute(2,0,1)

        return image_data, label


#preprocessing 예시(차후 proprecssing.py로 뺄 내용)
norm_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std = [0.5, 0.5, 0.5])
])

#jdbc connection
jdbc_connection = jaydebeapi.connect(
    tbdriver,
    database_url,
    [username, password],
    jdbc_driver_jar,
)

train_query = "SELECT label, image_data FROM t_training_data"
test_query = "SELECT label, image_data FROM t_test_data"
train_dataset = Classification_Dataset(True, jdbc_connection, train_query, norm_transform)
test_dataset = Classification_Dataset(False, jdbc_connection, test_query, norm_transform)

batch_size = 10

train_loader = Dataloader(
    train_dataset,
    batch_size = batch_size,
    shuffle = True,
    num_workers = 4,
)

test_loader = DataLoader(
    test_dataset,
    batch_size = batch_size,
    shuffle = False,
    num_workers = 4,
)