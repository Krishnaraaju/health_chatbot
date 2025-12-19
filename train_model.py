
import pandas as pd
import joblib
import json
import os
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

# Define paths (TARGETING TN DATASET)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAINING_DATA_PATH = os.path.join(BASE_DIR, "Data", "Training_TN.csv")
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "model.pkl")
ENCODER_SAVE_PATH = os.path.join(BASE_DIR, "encoder.pkl")
FEATURES_SAVE_PATH = os.path.join(BASE_DIR, "features.json")

def train_health_model():
    print(f"Loading 500-Disease Dataset: {TRAINING_DATA_PATH}")
    try:
        train_df = pd.read_csv(TRAINING_DATA_PATH)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    print(f"Dataset Shape: {train_df.shape}")
    
    X = train_df.iloc[:, :-1]
    y = train_df.iloc[:, -1]

    # Encode Labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    print(f"Classes found: {len(le.classes_)}")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.1, random_state=42)

    print("Training Decision Tree Classifier (Optimized for Memory)...")
    model = DecisionTreeClassifier(criterion='entropy', random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Validation Accuracy: {accuracy * 100:.2f}%")

    # Save
    print("Saving new brain...")
    joblib.dump(model, MODEL_SAVE_PATH)
    joblib.dump(le, ENCODER_SAVE_PATH)
    
    feature_names = list(X.columns)
    with open(FEATURES_SAVE_PATH, 'w') as f:
        json.dump(feature_names, f)

    print("Training Complete. The Chatbot is now powered by 500+ Diseases.")

if __name__ == "__main__":
    train_health_model()
