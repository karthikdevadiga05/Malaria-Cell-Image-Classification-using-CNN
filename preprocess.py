import os
import splitfolders
import cv2
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from PIL import Image

def create_directory_structure():
    """Create necessary directories for the project."""
    os.makedirs("static/uploads", exist_ok=True)
    os.makedirs("model", exist_ok=True)
    os.makedirs("dataset/processed", exist_ok=True)

def split_dataset(input_folder="dataset/cell_images", output_folder="dataset/processed", train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
    """Split the dataset into train, validation and test sets using splitfolders."""
    print("🔄 Splitting dataset...")
    splitfolders.ratio(input_folder, output=output_folder, ratio=(train_ratio, val_ratio, test_ratio), seed=42)
    print("✅ Dataset split complete.")
    return (
        os.path.join(output_folder, "train"),
        os.path.join(output_folder, "val"),
        os.path.join(output_folder, "test")
    )

def count_images(folder):
    """Count the total number of image files in a folder (recursively)."""
    return sum(len([f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]) for _, _, files in os.walk(folder))

def create_data_generators(train_folder, val_folder, test_folder, img_size=(224, 224), batch_size=32):
    """Create training, validation, and test data generators with preprocessing and augmentation."""
    print("⚙ Creating data generators...")
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=40,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    val_test_datagen = ImageDataGenerator(rescale=1./255)
    train_generator = train_datagen.flow_from_directory(
        train_folder,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical',   # <--- CHANGED
        color_mode='rgb',
        shuffle=True
    )
    val_generator = val_test_datagen.flow_from_directory(
        val_folder,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical',   # <--- CHANGED
        color_mode='rgb',
        shuffle=False
    )
    test_generator = val_test_datagen.flow_from_directory(
        test_folder,
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical',   # <--- CHANGED
        color_mode='rgb',
        shuffle=False
    )
    print("✅ Generators ready.")
    return train_generator, val_generator, test_generator

def visualize_samples(folder, num_samples=4, classes=["Parasitized", "Uninfected", "NotCell"]):
    """Visualize and save sample images from the training dataset."""
    plt.figure(figsize=(12, 6))
    for idx, class_name in enumerate(classes):
        class_path = os.path.join(folder, class_name)
        images = os.listdir(class_path)[:num_samples]
        for i, img_name in enumerate(images):
            img_path = os.path.join(class_path, img_name)
            img = cv2.imread(img_path)
            if img is None:
                continue
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            plt.subplot(len(classes), num_samples, idx * num_samples + i + 1)
            plt.imshow(img)
            plt.title(class_name)
            plt.axis("off")
    plt.tight_layout()
    plt.savefig("static/sample_images.png")
    plt.close()
    print("🖼 Saved visualization to static/sample_images.png")

if __name__== "__main__":
    create_directory_structure()
    train, val, test = split_dataset()
    create_data_generators(train, val, test)
    visualize_samples(train)
