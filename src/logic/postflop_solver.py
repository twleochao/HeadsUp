import xgboost as xgb
import numpy as np
import os
from typing import Dict

class PostflopSolver:
    def __init__(self, model_path: str = "models/postflop_xgb.json"):
        self.model_path = model_path
        self.model = None
        self.action_map = {
            0: "FOLD",
            1: "CHECK",
            2: "BET"
        }
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            print(f"Postflop model not found at {self.model_path}")
            return
        
        try:
            self.model = xgb.Booster()
            self.model.load_model(self.model_path)
            print(f"Successfully loaded postflop model from {self.model_path}")
        except Exception as e:
            print(f"ERROR loading postflop model: {e}")
            self.model = None

    def get_postflop_action(self, feature_vector: np.ndarray) -> Dict[str, str]:
        if self.model is None:
            return {"action": "NO MODEL", "amount_str": ""}
        
        try:
            dmatrix = xgb.DMatrix(feature_vector.reshape(1, -1))
            
            pred_class = self.model.predict(dmatrix)
            
            action_index = int(np.argmax(pred_class))
            
            action = self.action_map.get(action_index, "UNKNOWN")
            
            # TODO: We need the model to also predict bet *sizing*
            amount_str = ""
            if action == "BET":
                amount_str = "50% Pot"

            return {"action": action, "amount_str": amount_str}

        except Exception as e:
            print(f"error: {e}")
            return {"action": "ERROR", "amount_str": ""}