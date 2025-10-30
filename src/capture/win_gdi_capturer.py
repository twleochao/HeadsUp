import win32gui
import win32ui
import win32con
import numpy as np
import time
from typing import Optional

from src.capture.base_capturer import BaseCapturer, FrameData
from src.capture.utils import find_window_by_title

class WinGDICapturer(BaseCapturer):
    def __init__(self, target_window_title: str):
        super().__init__(target_window_title)
        self.w_dc: Optional[int] = None
        self.dc_obj: Optional[win32ui.DC] = None
        self.c_dc: Optional[win32ui.DC] = None
        self.data_bitmap: Optional[win32ui.BITMAP] = None
        self.client_offset_x: int = 0
        self.client_offset_y: int = 0

    def start(self) -> None:
        self.hwnd = find_window_by_title(self.target_window_title)
        if not self.hwnd:
            raise FileNotFoundError(f"Window not found: '{self.target_window_title}'")

        left, top, right, bot = win32gui.GetClientRect(self.hwnd)
        self.width = right - left
        self.height = bot - top
        
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                f"Window '{self.target_window_title}' has 0 size. "
                "Is it minimized?"
            )

        self.w_dc = win32gui.GetWindowDC(self.hwnd)
        self.dc_obj = win32ui.CreateDCFromHandle(self.w_dc)
        self.c_dc = self.dc_obj.CreateCompatibleDC()
        self.data_bitmap = win32ui.CreateBitmap()
        self.data_bitmap.CreateCompatibleBitmap(self.dc_obj, self.width, self.height)
        self.c_dc.SelectObject(self.data_bitmap)

        client_left_screen, client_top_screen = win32gui.ClientToScreen(self.hwnd, (left, top))
        win_left_screen, win_top_screen, _, _ = win32gui.GetWindowRect(self.hwnd)
        
        self.client_offset_x = client_left_screen - win_left_screen
        self.client_offset_y = client_top_screen - win_top_screen

    def stop(self) -> None:
        try:
            if self.dc_obj:
                self.dc_obj.DeleteDC()
            if self.c_dc:
                self.c_dc.DeleteDC()
            if self.w_dc and self.hwnd:
                win32gui.ReleaseDC(self.hwnd, self.w_dc)
            if self.data_bitmap:
                win32gui.DeleteObject(self.data_bitmap.GetHandle())
        except (win32ui.error, win32gui.error) as e:
            print(f"Error during GDI resource cleanup: {e}")
        
        self.w_dc = self.dc_obj = self.c_dc = self.data_bitmap = self.hwnd = None

    def grab(self) -> Optional[FrameData]:
        if not self.hwnd or not self.c_dc or not self.dc_obj:
            print("Error: Capture not started or window handle is invalid.")
            return None

        t_start = time.perf_counter()

        try:
            self.c_dc.BitBlt(
                (0, 0),
                (self.width, self.height),
                self.dc_obj,
                (self.client_offset_x, self.client_offset_y),
                win32con.SRCCOPY
            )

            bmp_str = self.data_bitmap.GetBitmapBits(True)
            
            frame_bgra = np.frombuffer(bmp_str, dtype=np.uint8).reshape(
                self.height, self.width, 4
            )
            
            t_end = time.perf_counter()
            latency_ms = (t_end - t_start) * 1000.0

            frame_bgr = frame_bgra[:, :, :3].copy()

            return FrameData(
                frame=frame_bgr,
                timestamp_acquire=t_end,
                capture_latency_ms=latency_ms
            )

        except (win32ui.error, win32gui.error) as e:
            print(f"Window capture error (GDI): {e}")
            self.stop()
            return None