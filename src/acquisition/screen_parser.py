import cv2
import pytesseract
import numpy as np
import mss
import json
from pathlib import Path
from typing import Dict, Any
from itertools import chain

class ScreenScraper:
    def __init__(self, config_path: str = "config.json"):
        config_path = Path(config_path)

        with open(config_path, 'r') as f:
            cfg = json.load(f)
        self.roi = cfg["main_roi"] 
        self.sub_rois = cfg.get("sub_rois", {})
        self.sct = mss.mss()

    def normalize_rois(self, val):
        if isinstance(val, dict):
            return [val]
        if isinstance(val, list):
            if any(isinstance(item, list) for item in val):
                return list(chain.from_iterable(val))
            return val
        return []

    def grab_frame(self):
        monitor = {
            "top": self.roi["y"],
            "left": self.roi["x"],
            "width": self.roi["w"],
            "height": self.roi["h"],
        }

        sct_img = self.sct.grab(monitor)
        img = np.array(sct_img)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def preprocess(self, img: np.ndarray):
        crops = {}
        for key, val in self.sub_rois.items():
            rois = self.normalize_rois(val)
            crops[key] = []
            for r in rois:
                x, y = int(r.get("x", 0)), int(r.get("y", 0))
                w, h = int(r.get("w", 0)), int(r.get("h", 0))
                sub = img[y:y+h, x:x+w]
                gray = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                crops[key].append(thresh)
        return crops 

    def do_ocr(self, img:np.ndarray, config: str = ""):
        return pytesseract.image_to_string(img, config=config).strip()

    def parse_text(self, raw: str, region: str):
        if region == "pot":
            digits = "".join(ch for ch in raw if ch.isdigit())
            return int(digits) if digits else None

        if region in ("flop", "turn", "river", "hand"):
            parts = raw.replace("\n", " ").split()
            return [p for p in parts if len(p) in (2, 3)]

        if region == "player_actions":
            tokens = raw.lower().replace(":", "").split()
            action = {}
            if "seat" in tokens:
                i = tokens.index("seat")
                action["seat"] = int(tokens[i+1]) if i+1 < len(tokens) and tokens[i+1].isdigit() else None
            for act in ("bet", "call", "raise", "fold", "check"):
                if act in tokens:
                    action["action"] = act
                    idx = tokens.index(act)
                    if idx+1 < len(tokens) and tokens[idx+1].isdigit():
                        action["amount"] = int(tokens[idx+1])
                    break
            return action
        
        return raw

    def get_game_frame(self):
        frame: Dict[str, Any] = {}
        img = self.grab_frame()
        crops = self.preprocess(img)

        for key, imgs in crops.items():
            parsed = [self.parse_text(self.do_ocr(im), key) for im in imgs]
            frame[key] = parsed if len(parsed) > 1 else (parsed[0] if parsed else None)

        community = []
        for sec in ("flop", "turn", "river"):
            val = frame.pop(sec, None)
            if isinstance(val, list):
                community.extend(val)
            elif val:
                community.append(val)
        frame["community_cards"] = community

        names = frame.pop("player_names", []) or []
        players = [{"seat": i+1, "name": nm} for i, nm in enumerate(names)]
        frame["players"] = players

        actions = frame.pop("last_action", []) or []

        for i, action in enumerate(actions):
            if i < len(players):
                players[i]["last_action"] = action

        frame["pot"] = frame.pop("pot", None)

        return frame


if __name__ == "__main__":
    scraper = ScreenScraper(config_path="config.json")
    frame = scraper.get_game_frame()
    print(frame)
