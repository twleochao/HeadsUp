import mss
import numpy as np
import time
import cv2
import win32gui
from typing import Optional, Dict

from src.capture.base_capturer import BaseCapturer, FrameData
from src.capture.utils import find_window_by_title

class MSSCapturer(BaseCapturer):
    def __init__(self, target_window_title: str):
        super().__init__(target_window_title)
        self.sct: Optional[mss.mss] = None
        self.monitor: Dict[str, int] = {}

    def start(self) -> None:
        self.hwnd = find_window_by_title(self.target_window_title)
        if not self.hwnd:
            raise FileNotFoundError(f"Window not found: '{self.target_window_title}'")

        try:
            client_left, client_top, client_right, client_bot = win32gui.GetClientRect(self.hwnd)
            client_top_left_screen = win32gui.ClientToScreen(self.hwnd, (client_left, client_top))
            client_bot_right_screen = win32gui.ClientToScreen(self.hwnd, (client_right, client_bot))

            self.monitor = {
                "top": client_top_left_screen[1],
                "left": client_top_left_screen[0],
                "width": client_bot_right_screen[0] - client_top_left_screen[0],
                "height": client_bot_right_screen[1] - client_top_left_screen[1],
            }

            self.width = self.monitor["width"]
            self.height = self.monitor["height"]
            
            if self.width <= 0 or self.height <= 0:
                raise ValueError(
                    f"Window '{self.target_window_title}' has 0 size. "
                    "Is it minimized?"
                )

            self.sct = mss.mss()

        except win32gui.error as e:
            raise FileNotFoundError(f"Error getting window coordinates: {e}. Is the window valid?")

    def stop(self) -> None:
        if self.sct:
            self.sct.close()
            self.sct = None

    def grab(self) -> Optional[FrameData]:
        if not self.sct:
            print("Error: MSS capture not started.")
            return None

        t_start = time.perf_counter()
        
        try:
            sct_img = self.sct.grab(self.monitor)
            t_end = time.perf_counter()
            latency_ms = (t_end - t_start) * 1000.0

            frame = np.frombuffer(sct_img.raw, dtype=np.uint8).reshape(
                sct_img.height, sct_img.width, 4)
            
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            return FrameData(
                frame=frame_bgr,
                timestamp_acquire=t_end,
                capture_latency_ms=latency_ms
            )

        except mss.exception.ScreenShotError as e:
            print(f"MSS capture error: {e}")