import time
import numpy as np
import threading
from typing import Optional

from windows_capture import WindowsCapture, Frame, InternalCaptureControl
from src.capture.base_capturer import BaseCapturer, FrameData

class WinDXGICapturer(BaseCapturer):
    def __init__(self, target_window_title: str):
        super().__init__(target_window_title)
        self.capture: Optional[WindowsCapture] = None
        self.last_frame: Optional[np.ndarray] = None
        self.last_timestamp: float = 0.0
        self.is_running: bool = False
        self.frame_lock: threading.Lock = threading.Lock()
        self.capture_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        try:
            self.capture = WindowsCapture(window_name=self.target_window_title)
            
            @self.capture.event
            def on_frame_arrived(frame: Frame, _: InternalCaptureControl):
                t_now = time.perf_counter()
                
                h = frame.height
                w = frame.width
                
                raw_buffer = frame.frame_buffer
                try:
                    frame_array_bgra = np.array(raw_buffer, copy=True, dtype=np.uint8)
                    frame_array = frame_array_bgra.reshape((h, w, 4))
                except Exception as e:
                    print(f"Error processing frame: {e}. Buffer len: {len(raw_buffer) if raw_buffer else 'None'}. Expected: {h*w*4}")
                    return

                with self.frame_lock:
                    if self.height != h or self.width != w:
                        if self.height == 0:
                            print(f"DXGI capture started for '{self.target_window_title}' ({w}x{h})")
                        else:
                            print(f"Window resized to: {w}x{h}")
                        self.height = h
                        self.width = w
                    
                    self.last_frame = frame_array
                    self.last_timestamp = t_now
                

            @self.capture.event
            def on_closed():
                print(f"Target window '{self.target_window_title}' was closed.")
                self.stop()
            
            self.capture_thread = threading.Thread(target=self.capture.start, daemon=True)
            self.capture_thread.start()
            self.is_running = True

        except Exception as e:
            raise RuntimeError(f"Failed to start DXGI capture: {e}")

    def stop(self) -> None:
        if self.capture and self.is_running:
            try:
                self.capture.stop()
            except Exception as e:
                print(f"Error stopping DXGI capture: {e}")
                
        self.capture = None
        with self.frame_lock:
            self.last_frame = None
        self.is_running = False
        print("DXGI capture stopped.")

    def grab(self) -> Optional[FrameData]:
        if not self.is_running:
            return None

        t_start = time.perf_counter()
        frame_bgra: Optional[np.ndarray] = None
        timestamp_acquire: float = 0.0

        with self.frame_lock:
            if self.last_frame is not None:
                frame_bgra = self.last_frame
                timestamp_acquire = self.last_timestamp
                self.last_frame = None

        if frame_bgra is None:
            return None
            
        frame_bgr = frame_bgra[:, :, :3].copy()
        
        t_end = time.perf_counter()
        latency_ms = (t_end - t_start) * 1000.0

        return FrameData(
            frame=frame_bgr,
            timestamp_acquire=timestamp_acquire,
            capture_latency_ms=latency_ms 
        )