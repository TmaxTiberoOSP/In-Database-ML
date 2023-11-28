import csv
from torchvision.datasets import CIFAR10
from torchvision import transforms
import os

def save_to_csv(dataset, csv_file_path):
    with open(csv_file_path, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['File Name', 'Label'])

        for i, (_, label) in enumerate(dataset):
            file_name = f"cifar10_{i}_{label}.jpg"
            csv_writer.writerow([file_name, label])

# Define a transform to normalize the data
transform = transforms.Compose([
    transforms.ToTensor(),
])

# Download the CIFAR-10 training dataset
train_dataset = CIFAR10(root='./data', train=True, download=True, transform=transform)

# Download the CIFAR-10 test dataset
test_dataset = CIFAR10(root='./data', train=False, download=True, transform=transform)

# Create output directories
output_dir_train = './cifar10_jpg_images/train'
output_dir_test = './cifar10_jpg_images/test'
os.makedirs(output_dir_train, exist_ok=True)
os.makedirs(output_dir_test, exist_ok=True)

# Save file names and labels to CSV for both training and test datasets
save_to_csv(train_dataset, './cifar10_labels_train.csv')
save_to_csv(test_dataset, './cifar10_labels_test.csv')

print(f"Training file names and labels saved to: './cifar10_labels_train.csv'")
print(f"Test file names and labels saved to: './cifar10_labels_test.csv'")