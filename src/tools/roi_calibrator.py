import cv2
import json
import mss
import numpy as np

rois = {}
current = {}
drawing = False

def mouse_cb(event, x, y, flags, param):
    global current, drawing
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        current["x1"], current["y1"] = x, y
    elif event == cv2.EVENT_LBUTTONMOVE and drawing:
        current["x2"], current["y2"] = x, y
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        current["x2"], current["y2"] = x, y
