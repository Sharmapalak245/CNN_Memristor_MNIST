import os
import numpy as np
import json

DATA_DIR = './kaggle_mnist'

# 1. Helper functions to read the raw binary IDX files
def read_raw_images(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'rb') as f:
        f.read(16) # Skip the 16-byte metadata header
        # Read the rest as unsigned 8-bit integers and reshape to 28x28
        return np.fromfile(f, dtype=np.uint8).reshape(-1, 28, 28)

def read_raw_labels(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'rb') as f:
        f.read(8) # Skip the 8-byte metadata header
        return np.fromfile(f, dtype=np.uint8)

print("Reading raw binary files...")

# 2. Load the untouched data directly into memory
train_images = read_raw_images('train-images-idx3-ubyte')
train_labels = read_raw_labels('train-labels-idx1-ubyte')
test_images = read_raw_images('t10k-images-idx3-ubyte')
test_labels = read_raw_labels('t10k-labels-idx1-ubyte')

# 3. Gather all characteristics into a standard dictionary
# Note: We must cast numpy types (like np.uint8) to standard int() or str() for JSON compatibility
dataset_info = {
    "dataset_overview": {
        "source_directory": DATA_DIR,
        "total_training_samples": int(train_images.shape[0]),
        "total_testing_samples": int(test_images.shape[0]),
        "raw_data_type": str(train_images.dtype)
    },
    "training_set_characteristics": {
        "image_dimensions": [int(train_images.shape[1]), int(train_images.shape[2])],
        "pixel_value_min": int(train_images.min()),
        "pixel_value_max": int(train_images.max()),
        "label_array_length": int(train_labels.shape[0]),
        "unique_classes_found": [int(c) for c in np.unique(train_labels)]
    },
    "testing_set_characteristics": {
        "image_dimensions": [int(test_images.shape[1]), int(test_images.shape[2])],
        "pixel_value_min": int(test_images.min()),
        "pixel_value_max": int(test_images.max()),
        "label_array_length": int(test_labels.shape[0])
    }
}

# 4. Save the characteristics to a JSON file
output_filename = 'dataset_info.json'
with open(output_filename, 'w') as json_file:
    json.dump(dataset_info, json_file, indent=4)

print(f"Success! Raw characteristics have been extracted and saved to '{output_filename}'.")