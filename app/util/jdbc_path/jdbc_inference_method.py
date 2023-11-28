import jaydebeapi
from PIL import Image
import io
from torchvision import transforms
import numpy as np
from io import BytesIO
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

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

#tibero의 table과 blob column이 이렇게 되어있다고 가정
table_name = 'model_storage'
blob_column = 'model_data'


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

cursor.execute(f"SELECT {blob_column} FROM {table_name}")
model_data = cursor.fetchone()[0]

#Load model from bin data
model = torch.load(BytesIO(model_data))
#set model to evaluation model
model.eval()

# Close the database connection
cursor.close()
connection.close()

###############single image inference#############################
# We assume target image is "000.jpg" in table "my_table"
image_name = "000.jpg"

jdbc_connection = jaydebeapi.connect(
        "com.tmax.tibero.jdbc.TbDriver",
        database_url,
        [username, password],
        jdbc_driver_jar,
)
# Create a cursor
cursor = jdbc_connection.cursor()

# Example SQL query to select image data from the table
select_image_query = "SELECT image_data FROM my_table WHERE image_name = ?"

# Execute the select image query with the image ID as a parameter
cursor.execute(select_image_query, [image_name])


# Fetch the image data
image_data = cursor.fetchone()[0]

image = Image.open(BytesIO(image_data))

# Preprocess the image
transform = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
])

preprocessed_image = transform(image).unsqueeze(0)

with torch.no_grad():
    classification_result = model(preprocessed_image)

# Get the predicted class
predicted_class = torch.argmax(output).item()

# Print the result
print(f"Predicted Class: {predicted_class}")


###############test Dataloader inference#############################
# Here use the test_dataloader to check model's accuracy

# Evaluate the model on the test set
model.eval()

# Define lists to store true labels and predicted labels
true_labels = []
predicted_labels = []

# Perform inference on the test loader
with torch.no_grad():
    for images, labels in test_loader:
        outputs = model(images)
        _, predicted = torch.max(outputs, 1)

        true_labels.extend(labels.numpy())
        predicted_labels.extend(predicted.numpy())

# Calculate accuracy
accuracy = accuracy_score(true_labels, predicted_labels)
print(f'Accuracy: {accuracy}')

# Calculate classification report
class_report = classification_report(true_labels, predicted_labels)
print(f'Classification Report:\n{class_report}')

# Calculate confusion matrix
conf_matrix = confusion_matrix(true_labels, predicted_labels)
print(f'Confusion Matrix:\n{conf_matrix}')

