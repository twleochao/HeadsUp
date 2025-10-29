import numpy as np
import time
from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict
from typing import Optional

class FrameData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    frame: np.ndarray
    timestamp_acquire: float
    capture_latency_ms: float

class BaseCapturer(ABC):
    def __init__(self, target_window_title: str):
        self.target_window_title = target_window_title
        self.hwnd: Optional[int] = None
        self.width: int = 0
        self.height: int = 0

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def grab(self) -> Optional[FrameData]:
        pass

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()