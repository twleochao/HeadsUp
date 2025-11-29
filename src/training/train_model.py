import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os

DATASET_PATH = "data/training_dataset.csv"
MODEL_SAVE_PATH = "models/postflop_xgb.json"
NUM_CLASSES = 3

def main():
    print(f"Loading dataset from {DATASET_PATH}...")
    try:
        dataset = pd.read_csv(DATASET_PATH)
    except FileNotFoundError:
        print(f"ERROR: Dataset not found. Run 'python training/data_generator.py' first.")
        return

    X = dataset.iloc[:, :-1].values
    y = dataset.iloc[:, -1].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"Training XGBoost model on {len(X_train)} samples...")

    model = xgb.XGBClassifier(
        objective='multi:softmax',
        num_class=NUM_CLASSES,
        eval_metric='mlogloss',
        use_label_encoder=False,
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8
    )

    model.fit(X_train, y_train)

    print("Training complete.")

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n--- Model Evaluation ---")
    print(f"Test Accuracy: {accuracy * 100.0:.2f}%")

    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    model.save_model(MODEL_SAVE_PATH)
    print(f"\nSuccessfully trained and saved model to {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    main()