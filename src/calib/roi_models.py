import json
import os
from pydantic import BaseModel, Field
from typing import Dict, Tuple, Any

Rect = Tuple[int, int, int, int]
Point = Tuple[int, int]
PropRect = Tuple[float, float, float, float]

class RoiProfile(BaseModel):
    profile_name: str
    
    master_resolution: Tuple[int, int] = Field(..., description="Absolute (w, h) of game window at calibration")
    board_rect: PropRect
    pot_rect: PropRect
    seat_rects: Dict[int, PropRect]

    def save_json(self, filepath: str) -> None:
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(self.model_dump(), f, indent=2)
            print(f"Success! ROI profile saved to {filepath}")
        except IOError as e:
            print(f"Error saving ROI profile to {filepath}: {e}")
            raise

    @classmethod
    def load_json(cls, filepath: str) -> 'RoiProfile':
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return cls(**data)
        except FileNotFoundError:
            print(f"Error: ROI profile not found at {filepath}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred loading {filepath}: {e}")
            raise

    def get_rects_for_resolution(self, new_w: int, new_h: int) -> Dict[str, Any]:
        orig_w, orig_h = self.master_resolution
        ratio = min(new_w / orig_w, new_h / orig_h)
        
        scaled_w = int(orig_w * ratio)
        scaled_h = int(orig_h * ratio)
        
        offset_x = (new_w - scaled_w) // 2
        offset_y = (new_h - scaled_h) // 2
        
        def _to_pixels(pr: PropRect) -> Rect:
            px = int(pr[0] * scaled_w) + offset_x
            py = int(pr[1] * scaled_h) + offset_y
            pw = int(pr[2] * scaled_w)
            ph = int(pr[3] * scaled_h)
            return (px, py, pw, ph)

        board_pixel_rect = _to_pixels(self.board_rect)
        
        return {
            "master": (offset_x, offset_y, scaled_w, scaled_h),
            "board_area": board_pixel_rect,
            "pot": _to_pixels(self.pot_rect),
            "seats": {
                seat_id: _to_pixels(prop_rect)
                for seat_id, prop_rect in self.seat_rects.items()
            }
        }