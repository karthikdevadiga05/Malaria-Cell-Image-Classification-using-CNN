import os
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
from preprocess import split_dataset, create_data_generators
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns

# Constants
EPOCHS = 30
BATCH_SIZE = 16
IMG_SIZE = (224,224)
DATASET_DIR = "dataset/cell_images"
PROCESSED_DATASET_DIR = "dataset/processed"
MODEL_PATH = "model/malaria_model.keras"

# Dataset prep
split_dataset()
train_folder = os.path.join(PROCESSED_DATASET_DIR, "train")
val_folder = os.path.join(PROCESSED_DATASET_DIR, "val")
test_folder = os.path.join(PROCESSED_DATASET_DIR, "test")

train_gen, val_gen, test_gen = create_data_generators(
    train_folder, val_folder, test_folder,
    batch_size=BATCH_SIZE,
    img_size=IMG_SIZE
)

print("Class indices:", train_gen.class_indices, flush=True)
class_labels = list(train_gen.class_indices.keys())

# Model
model = Sequential([
    Input(shape=(*IMG_SIZE, 3)),
    Conv2D(32, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),
    BatchNormalization(),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),
    BatchNormalization(),
    Conv2D(128, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),
    BatchNormalization(),
    Conv2D(256, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),
    BatchNormalization(),
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.4),
    Dense(3, activation='softmax')   # <--- CHANGED
])

model.compile(
    optimizer=Adam(learning_rate=0.0001), 
    loss='categorical_crossentropy',   # <--- CHANGED
    metrics=['accuracy']
)

# Save model summary to file
model.summary(print_fn=lambda x: open("model_summary.txt", "a", encoding="utf-8").write(x + "\n"))

# Calculate class weights for handling imbalance
train_labels = train_gen.classes
class_weights = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(train_labels),
    y=train_labels
)
class_weight_dict = dict(enumerate(class_weights))

# Callbacks
checkpoint = ModelCheckpoint(MODEL_PATH, save_best_only=True)
early_stop = EarlyStopping(patience=10, restore_best_weights=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=1e-6, verbose=1)

# Train
history = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=EPOCHS,
    callbacks=[early_stop, checkpoint, reduce_lr],
    class_weight=class_weight_dict
)

print(f"✅ Best model saved at: {MODEL_PATH}")

# Evaluate
results = model.evaluate(val_gen)
print(f"Validation Loss: {results[0]:.4f}")
print(f"Validation Accuracy: {results[1] * 100:.2f}%")

# Visuals
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.legend()
plt.title('Model Accuracy')

plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.legend()
plt.title('Model Loss')
plt.tight_layout()
plt.savefig('static/training_curves.png')
plt.show()

# Confusion matrix
print("\nEvaluating on test data...")
test_gen.reset()
y_pred = model.predict(test_gen, steps=len(test_gen), verbose=1)
y_pred_classes = np.argmax(y_pred, axis=1)
y_true = test_gen.classes

cm = confusion_matrix(y_true, y_pred_classes)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=class_labels, yticklabels=class_labels)
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.savefig('static/confusion_matrix.png')
plt.show()

print("\nClassification Report:")
print(classification_report(y_true, y_pred_classes, target_names=class_labels))
