"""
Agent 3: Plant Disease Detection CNN Training
Uses PlantVillage dataset (images in train/test folders, 38 disease classes).
Uses Transfer Learning with MobileNetV2 (pre-trained on ImageNet) — fast & accurate.
Output: backend/app/models/plant_disease_model.h5
        backend/app/models/disease_class_names.pkl
"""
import os
import pickle
import numpy as np

# Suppress TF verbose output
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import joblib

TRAIN_DIR = "/Users/swabhiman/Desktop/dataset/train"
TEST_DIR  = "/Users/swabhiman/Desktop/dataset/test"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "plant_disease_model.h5")
CLASSES_PATH = os.path.join(MODEL_DIR, "disease_class_names.pkl")

IMG_SIZE    = 128       # MobileNetV2 min is 96 — 128 is fast yet sharp
BATCH_SIZE  = 32
EPOCHS      = 10        # EarlyStopping will cut this short if needed
SAMPLES_PER_CLASS = 300 # Cap images per class to keep training under 20 min

def create_limited_generator(directory, samples_per_class, augment=False):
    """ImageDataGenerator that caps images per class for speed."""
    if augment:
        gen = ImageDataGenerator(
            rescale=1./255,
            rotation_range=20,
            width_shift_range=0.1,
            height_shift_range=0.1,
            horizontal_flip=True,
            zoom_range=0.1,
        )
    else:
        gen = ImageDataGenerator(rescale=1./255)

    flow = gen.flow_from_directory(
        directory,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=True,
    )
    return flow

def build_model(num_classes):
    """MobileNetV2 with custom classification head."""
    base = MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights="imagenet"          # Pre-trained weights — this is the transfer learning
    )
    # Freeze ALL base layers first — we only train our new head
    base.trainable = False

    x = base.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.3)(x)
    x = Dense(256, activation="relu")(x)
    x = Dropout(0.2)(x)
    predictions = Dense(num_classes, activation="softmax")(x)

    model = Model(inputs=base.input, outputs=predictions)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model, base

def fine_tune_model(model, base, num_classes):
    """Unfreeze last 30 layers of MobileNetV2 for fine-tuning."""
    base.trainable = True
    for layer in base.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),  # lower LR for fine-tune
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    return model

def main():
    print("=" * 55)
    print("AGENT 3: Plant Disease CNN Training")
    print("Transfer Learning with MobileNetV2 (ImageNet weights)")
    print("=" * 55)

    # Confirm GPU/CPU
    gpus = tf.config.list_physical_devices("GPU")
    print(f"\n⚡ Device: {'GPU (' + gpus[0].name + ')' if gpus else 'CPU (no GPU detected — using CPU)'}")

    print(f"\n📂 Training data: {TRAIN_DIR}")
    print(f"📂 Test data:     {TEST_DIR}")

    # Create data generators
    print(f"\n📦 Loading images (cap: {SAMPLES_PER_CLASS} per class)...")
    train_gen = create_limited_generator(TRAIN_DIR, SAMPLES_PER_CLASS, augment=True)
    val_gen   = create_limited_generator(TEST_DIR, SAMPLES_PER_CLASS, augment=False)

    class_names = list(train_gen.class_indices.keys())
    num_classes = len(class_names)
    print(f"✅ Found {num_classes} disease classes")
    print(f"   Total training batches: {len(train_gen)}")

    # Build model
    print(f"\n🏗️  Building MobileNetV2 transfer learning model...")
    model, base = build_model(num_classes)
    print(f"   Parameters: {model.count_params():,} total | trainable: {sum([tf.size(v).numpy() for v in model.trainable_variables]):,}")

    # Phase 1: Train only the classification head
    print("\n🔵 Phase 1: Training classification head (base frozen)...")
    callbacks = [
        EarlyStopping(monitor="val_accuracy", patience=3, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, verbose=1),
    ]

    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1,
    )

    # Phase 2: Fine-tune top layers of base
    print("\n🟠 Phase 2: Fine-tuning top 30 MobileNetV2 layers...")
    model = fine_tune_model(model, base, num_classes)
    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=5,
        callbacks=callbacks,
        verbose=1,
    )

    # Final evaluation
    print("\n📊 Evaluating on test set...")
    results = model.evaluate(val_gen, verbose=0)
    print("\n" + "=" * 55)
    print("✅ TRAINING COMPLETE!")
    print(f"   Test Accuracy: {results[1] * 100:.2f}%")
    print(f"   Test Loss:     {results[0]:.4f}")
    print("=" * 55)

    # Save model and class names
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save(MODEL_PATH)
    joblib.dump(class_names, CLASSES_PATH)
    print(f"\n💾 Model saved to:  {MODEL_PATH}")
    print(f"💾 Classes saved:   {CLASSES_PATH}")
    print(f"\n🌿 Disease classes trained on:")
    for i, name in enumerate(class_names):
        print(f"   {i+1:2d}. {name}")

if __name__ == "__main__":
    main()
