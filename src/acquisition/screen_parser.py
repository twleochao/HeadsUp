import cv2
import pytesseract
import numpy as np
import mss
from typing import Dict, Any

class ScreenScraper:
    def __init__(self, roi: Dict[str, int], sub_rois: Dict[str, Dict]):
        self.roi = roi
        self.sct = mss.mss()
        self.sub_rois = sub_rois

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

    def preprocess(self, img: np.ndarry):
        crops = {}
        for key, r in self.sub_rois.items():
            x, y, w, h = r["x"], r["y"], r["w"], r["h"]
            sub = img[y:y+h, x:x+w]
            gray = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            crops[key] = thresh

        return img

    def do_ocr(self, img:np.ndarray, config: str):
        return pytesseract.image_to_string(img, config=config).strip()

    def parse_text(self, raw: str, region: str):
        if region == "pot":
            digits = "".join(ch for ch in raw if ch.isdigit())
            return int(digits) if digits else None
        elif region in ("flop", "turn", "river", "hand"):
            return raw.split()
        elif region == "player_names":
            return raw
        return raw

    def get_game_frame(self):
        frame: Dict[str, Any] = {}
        img = self.grab_frame()
        crops = self.preprocess(img)

        for key, crop_img in crops.items():
            text = self.do_ocr(crop_img)
            parsed = self.parse_text(text, key)
            frame[key] = parsed

        return frame


if __name__ == "__main__":
    roi = {"x": 100, "y": 100, "w": 800, "h": 600} #fill out 
    scraper = ScreenScraper(roi)
