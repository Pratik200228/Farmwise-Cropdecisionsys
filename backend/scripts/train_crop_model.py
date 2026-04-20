"""
Agent 1: Crop Recommendation Model Training
Uses Crop_recommendation.csv (2200 rows) with N, P, K, temperature, humidity, pH, rainfall.
Trains a RandomForestClassifier to predict the best crop.
Output: backend/app/models/crop_recommendation_model.pkl
        backend/app/models/crop_label_encoder.pkl
"""
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib

DATA_PATH = "/Users/swabhiman/Desktop/Crop_recommendation.csv"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "crop_recommendation_model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "crop_label_encoder.pkl")

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
TARGET = "label"

def main():
    print("=" * 50)
    print("AGENT 1: Crop Recommendation Model Training")
    print("=" * 50)

    print(f"\n📂 Loading data from:\n   {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"✅ Loaded {len(df)} rows with {df[TARGET].nunique()} unique crops")
    print(f"   Crops: {sorted(df[TARGET].unique())}")

    X = df[FEATURES]
    y = df[TARGET]

    # Encode crop labels to integers
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # 80/20 split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    print(f"\n📊 Training set: {len(X_train)} rows | Test set: {len(X_test)} rows")

    print("\n🌲 Training Random Forest Classifier (200 trees)...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        n_jobs=-1  # use all CPU cores
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print("\n" + "=" * 50)
    print("✅ TRAINING COMPLETE!")
    print(f"   Accuracy: {acc * 100:.2f}%")
    print("=" * 50)
    print("\nPer-class breakdown:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # Save model and encoder
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)
    print(f"\n💾 Model saved to:   {MODEL_PATH}")
    print(f"💾 Encoder saved to: {ENCODER_PATH}")

if __name__ == "__main__":
    main()
