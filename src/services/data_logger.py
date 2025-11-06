import os
import csv
from PySide6.QtCore import QObject, Slot
from datetime import datetime

class DataLogger(QObject):
    def __init__(self, log_dir: str = "data/logs"):
        super().__init__()
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
        session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"session_{session_time}.csv")
        
        self._init_csv()

    def _init_csv(self):
        header = [
            "timestamp", "hand_id", "street", "hero_cards", "hero_pos",
            "board_cards", "pot_value", "hero_action", "gto_action"
        ]
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
        print(f"Logging session to {self.log_file}")

    @Slot(dict)
    def log_decision(self, data: dict):
        try:
            row = [
                data.get("timestamp", datetime.now().isoformat()),
                data.get("hand_id", "N/A"),
                data.get("street", "N/A"),
                data.get("hero_cards", "N/A"),
                data.get("hero_pos", "N/A"),
                data.get("board_cards", "N/A"),
                data.get("pot_value", 0),
                data.get("hero_action", "N/A"),
                data.get("gto_action", "N/A")
            ]
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except Exception as e:
            print(f"Error in DataLogger: {e}")