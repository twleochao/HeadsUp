import cv2
import argparse
import numpy as np
from typing import List, Tuple, Dict, Any

from src.capture.win_dxgi_capturer import WinDXGICapturer
from src.capture.utils import list_windows
from src.calib.roi_models import RoiProfile, Rect, PropRect, Point

def make_rect_from_clicks(pt1: Point, pt2: Point) -> Rect:
    x = min(pt1[0], pt2[0])
    y = min(pt1[1], pt2[1])
    w = abs(pt1[0] - pt2[0])
    h = abs(pt1[1] - pt2[1])
    return (x, y, w, h)

def to_proportional(pixel_rect: Rect, master_rect: Rect) -> PropRect:
    px, py, pw, ph = pixel_rect
    mx, my, mw, mh = master_rect
    
    if mw == 0 or mh == 0:
        return (0.0, 0.0, 0.0, 0.0)
        
    prx = (px - mx) / mw
    pry = (py - my) / mh
    prw = pw / mw
    prh = ph / mh
    return (prx, pry, prw, prh)

class CalibrationWizard:
    def __init__(self, window_title: str):
        self.window_title = window_title
        self.capturer = WinDXGICapturer(target_window_title=window_title)
        
        self.clicks: Dict[str, List[Point]] = {}
        self.window_name = "Calibration Wizard"
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        
        self.steps = [
            ("master", 2, "Click TL/BR of the ENTIRE Game Area (black box)"),
            ("board_area", 2, "Click TL/BR of the Full Board (Flop 1 to River)"),
            ("pot", 2, "Click TL/BR of the Pot Area"),
            ("hero_seat", 2, "Click TL/BR for HERO'S Seat Box"),
        ]
        
        self.current_step_index = 0
        self.current_seat_index = 1
        self.in_seat_loop = False

    def _get_current_step(self) -> Tuple[str, int, str]:
        if not self.in_seat_loop:
            step_name, clicks, prompt = self.steps[self.current_step_index]
            return step_name, clicks, prompt
        else:
            prompt = f"Click TL/BR for Seat {self.current_seat_index} (or 'n' to finish)"
            step_name = f"seat_{self.current_seat_index}"
            return step_name, 2, prompt

    def _mouse_callback(self, event: int, x: int, y: int, flags: int, param: Any):
        if event != cv2.EVENT_LBUTTONDOWN:
            return
            
        step_name, clicks_needed, _ = self._get_current_step()

        if step_name not in self.clicks:
            self.clicks[step_name] = []
            
        self.clicks[step_name].append((x, y))
        print(f"  > Click {len(self.clicks[step_name])}/{clicks_needed} recorded for {step_name} at ({x}, {y})")

        if len(self.clicks[step_name]) == clicks_needed:
            print(f"  > Step '{step_name}' complete.")
            
            if self.in_seat_loop:
                self.current_seat_index += 1
            else:
                self.current_step_index += 1

            if not self.in_seat_loop and self.current_step_index == len(self.steps):
                self.in_seat_loop = True
                print("\n--- Starting Seat Loop ---")
                print("Calibrate all other seats, starting from Hero's LEFT and going CLOCKWISE.")
                print("Press 'n' in the OpenCV window to finish calibration.\n")

    def run(self) -> None:
        try:
            with self.capturer as cap:
                cv2.namedWindow(self.window_name)
                cv2.setMouseCallback(self.window_name, self._mouse_callback)
                
                print("Starting calibration wizard...")
                
                while True:
                    frame_data = cap.grab()
                    if not frame_data:
                        continue
                    
                    frame = frame_data.frame
                    step_name, clicks_needed, prompt = self._get_current_step()

                    cv2.putText(frame, prompt, (50, 50), self.font, 1.0, (0, 255, 255), 2)
                    if self.in_seat_loop:
                        cv2.putText(frame, "Press 'n' to finish.", (50, 90), self.font, 0.7, (0, 255, 255), 2)

                    for name, points in self.clicks.items():
                        if len(points) == 2:
                            rect = make_rect_from_clicks(points[0], points[1])
                            color = (0, 255, 0) if name != 'master' else (0, 0, 255)
                            cv2.rectangle(frame, (rect[0], rect[1]), (rect[0]+rect[2], rect[1]+rect[3]), color, 2)

                    cv2.imshow(self.window_name, frame)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("Calibration cancelled.")
                        return
                    if key == ord('n') and self.in_seat_loop:
                        print("Calibration complete. Processing ROIs...")
                        self.process_rois(frame)
                        break

        except (RuntimeError, FileNotFoundError) as e:
            print(f"Error: {e}")
        finally:
            cv2.destroyAllWindows()

    def process_rois(self, frame: np.ndarray):
        """Derives all ROIs from the clicked anchor points."""
        try:
            master_rect = make_rect_from_clicks(self.clicks["master"][0], self.clicks["master"][1])
            master_w, master_h = master_rect[2], master_rect[3]
            
            board_rect = to_proportional(make_rect_from_clicks(self.clicks["board_area"][0], self.clicks["board_area"][1]), master_rect)
            pot_rect = to_proportional(make_rect_from_clicks(self.clicks["pot"][0], self.clicks["pot"][1]), master_rect)
            
            seat_rects: Dict[int, PropRect] = {}
            
            seat_rects[0] = to_proportional(make_rect_from_clicks(self.clicks["hero_seat"][0], self.clicks["hero_seat"][1]), master_rect)
            
            for i in range(1, self.current_seat_index):
                seat_key = f"seat_{i}"
                if seat_key in self.clicks:
                    seat_rects[i] = to_proportional(make_rect_from_clicks(self.clicks[seat_key][0], self.clicks[seat_key][1]), master_rect)
            
            profile_name = f"pokernow_{master_w}x{master_h}"
            
            profile = RoiProfile(
                profile_name=profile_name,
                master_resolution=(master_w, master_h),
                board_rect=board_rect,
                pot_rect=pot_rect,
                seats_rects=seat_rects
            )
            
            save_path = f"data/{profile_name}.json"
            profile.save_json(save_path)
            
            print(f"Calibrated {len(seat_rects)} seats.")
            
        except KeyError as e:
            print(f"Error: A calibration step was missed: {e}. Profile not saved.")
        except Exception as e:
            print(f"An unexpected error occurred during processing: {e}. Profile not saved.")

def main():
    parser = argparse.ArgumentParser(description="ROI Calibration Wizard")
    parser.add_argument(
        "-t", "--title",
        type=str,
        default=None, # Default to PokerNow
        help="Target window title. List of avaliable windows will be shown"
    )
    args = parser.parse_args()
    title = args.title
    windows = list_windows()

    if not title:
        print("No window title provided. Available windows:")
        windows = list_windows()
        if not windows:
            print("No visible windows found.")
            return
            
        for i, (hwnd, win_title) in enumerate(windows.items()):
            print(f"  {i+1}: {win_title}")
        
        try:
            choice = int(input("Enter the number of the window to capture: ")) - 1
            if 0 <= choice < len(windows):
                title = list(windows.values())[choice]
            else:
                print("Invalid choice.")
                return
        except ValueError:
            print("Invalid input.")
            return

    print(f"Starting wizard for: '{title}'")
    wizard = CalibrationWizard(window_title=title)
    wizard.run()

if __name__ == "__main__":
    main()