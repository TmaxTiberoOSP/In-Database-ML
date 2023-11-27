import jaydebeapi
from PIL import Image
import io
from torchvision import transforms
import numpy as np
from io import BytesIO

#torch
import torch
from torch.utils.data import Dataset, Dataloader
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

#dataloader
from jdbc_dataloader import train_loader, test_loader


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



class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()

        self.layer = nn.Sequential(
            nn.Conv2d(in_channels=3, out_channels=64, kernel_size=5),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(in_channels=64, out_channels=30, kernel_size=5),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Flatten(),
            nn.Linear(in_features=30*5*5, out_features=128, bias=True),
            nn.ReLU(inplace=True),
            nn.Linear(in_features=128, out_features=10, bias=True),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        x = self.layer(x)
        return x

net = Net()
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)
iteration_num = 100

for epoch in range(iteration_num):  # loop over the dataset multiple times

    running_loss = 0.0
    for i, data in enumerate(train_loader, 0):
        # get the inputs
        inputs, labels = data

        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
        outputs = net(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        # print statistics
        running_loss += loss.item()
        if i % 2000 == 1999:    # print every 2000 mini-batches
            print('[%d, %5d] loss: %.3f' %
                  (epoch + 1, i + 1, running_loss / 2000))
            running_loss = 0.0

print('Finished Training')

#경로&대상 지정
model_bytes = torch.save(net.state_dict(), BytesIO())

# Establish a connection to the Tibero database
#jdbc connection
jdbc_connection = jaydebeapi.connect(
    tbdriver,
    database_url,
    [username, password],
    jdbc_driver_jar,
)

connection = jdbc_connection 
cursor = connection.cursor()

#tibero의 table과 blob column이 이렇게 되어있다고 가정
table_name = 'model_storage'
blob_column = 'model_data'

insert_query = f"INSERT INTO {table_name} ({blob_column}) VALUES (?)"
cursor.execute(insert_query, model_bytes.getvalue())
connection.commit()

# Close the database connection
cursor.close()
connection.close()