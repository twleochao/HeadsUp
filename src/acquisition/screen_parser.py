import cv2
import pytesseract
import numpy as np
import mss
from typing import Dict

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
        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return bgr

    def preprocess(self, img: np.ndarry):
        crops = {}
        for key, r in self.sub_rois.items():
            x, y, w, h = r["x"], r["y"], r["w"], r["h"]
            sub = img[y:y+h, x:x+w]
            gray = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            crops[key] = thresh

        return img

    def do_ocr(self, img):
        # TODO: pytesseract.image_to_string(img, config=...)
        return ""

    def parse_text(self, raw: str):
        # TODO: regex or heuristics to extract numbers, card codes, names
        return {}

    def get_game_frame(self):
        img = self.grab_frame()
        prep = self.preprocess(img)
        text = self.do_ocr(prep)
        frame = self.parse_text(text)
        return frame


if __name__ == "__main__":
    roi = {"x": 100, "y": 100, "w": 800, "h": 600} #fill out 
    scraper = ScreenScraper(roi)
