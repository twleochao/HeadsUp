import time
import numpy as np
import warnings
from typing import Optional
from windows_capture import WindowsCapture, Frame, CaptureControl

from src.capture.base_capturer import BaseCapturer, FrameData
from src.capture.utils import find_window_by_title

class WinDXGICapturer(BaseCapturer):
    def __init__(self, target_window_title: str):
        super().__init__(target_window_title)
        self.capture: Optional[WindowsCapture] = None
        self.last_frame: Optional[np.ndarray] = None
        self.last_timestamp: float = 0.0
        self.is_running: bool = False

    def _on_frame(self, frame: Frame, _):
        t_now = time.perf_counter()
        
        self.last_frame = frame.to_ndarray()
        self.last_timestamp = t_now
        frame.release()

    def _on_closed(self):
        print(f"Target window '{self.target_window_title}' was closed.")
        self.stop()

    def start(self) -> None:
        self.hwnd = find_window_by_title(self.target_window_title)
        if not self.hwnd:
            raise FileNotFoundError(f"Window not found: '{self.target_window_title}'")
            
        try:
            self.capture = WindowsCapture(window_handle=self.hwnd)
            self.width = self.capture.width
            self.height = self.capture.height

            if self.width <= 0 or self.height <= 0:
                warnings.warn(f"Window '{self.target_window_title}' has 0 size. ")

            self.capture.on_frame_arrived(self._on_frame)
            self.capture.on_closed(self._on_closed)
            
            CaptureControl.start_capture(self.capture)
            self.is_running = True
            print(f"DXGI capture started for HWND {self.hwnd} ({self.width}x{self.height})")

        except Exception as e:
            raise RuntimeError(f"Failed to start DXGI capture: {e}")

    def stop(self) -> None:
        if self.capture and self.is_running:
            try:
                CaptureControl.stop_capture(self.capture)
            except Exception as e:
                print(f"Error stopping DXGI capture: {e}")
                
        self.capture = None
        self.last_frame = None
        self.is_running = False
        print("DXGI capture stopped.")

    def grab(self) -> Optional[FrameData]:
        if not self.is_running or self.last_frame is None:
            return None

        t_start = time.perf_counter()

        frame_bgra = self.last_frame
        timestamp_acquire = self.last_timestamp
        
        self.last_frame = None

        if frame_bgra is None:
            return None
            
        frame_bgr = frame_bgra[:, :, :3].copy()
        
        self.height, self.width, _ = frame_bgr.shape

        t_end = time.perf_counter()
        
        latency_ms = (t_end - t_start) * 1000.0

        return FrameData(
            frame=frame_bgr,
            timestamp_acquire=timestamp_acquire,
            capture_latency_ms=latency_ms 
        )