import torchvision.transforms as transforms
import torchvision.datasets as datasets
from torch.utils.data import DataLoader

def get_dataloader():
    """
    Loads the MNIST dataset with the specific padding and channel 
    requirements needed for the MNSIM LeNet hardware blueprint.
    """
    
    # 1. The precise transformations dictated by network.py
    mnsim_lenet_transform = transforms.Compose([
        transforms.Pad(2),                           # Expands 28x28 MNIST to the required 32x32
        transforms.Grayscale(num_output_channels=3), # Fakes the required 3 channels
        transforms.ToTensor()                        # Automatically applies the exact 1./255. activation_scale
    ])

    # 2. Applying it to your dataset
    train_dataset = datasets.MNIST(
        root='./kaggle_mnist', 
        train=True, 
        download=True, 
        transform=mnsim_lenet_transform
    )

    test_dataset = datasets.MNIST(
        root='./kaggle_mnist', 
        train=False, 
        download=True,  
        transform=mnsim_lenet_transform
    )

    # 3. DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True)
    
    # Batch size 1 is standard for MNSIM hardware evaluation
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False) 

    # MNSIM interface expects a tuple of (train_loader, test_loader)
    return train_loader, test_loader

if __name__ == '__main__':
    print("Testing data loader...")
    train, test = get_dataloader()
    print(f"Success! Train batches: {len(train)}, Test batches: {len(test)}")