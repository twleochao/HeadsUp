import cv2
import json
import argparse
from typing import List, Tuple, Dict, Any

from src.capture.win_dxgi_capturer import WinDXGICapturer
from src.capture.utils import list_windows
from src.calib.roi_models import RoiProfile, BoardROIs, SeatROIs, DealerButtonROI, Rect

CARD_WIDTH = 80
CARD_HEIGHT = 110
CARD_OFFSET_X = 90 

BOARD_GEOMETRY = {
    "flop_1": (0, 0, CARD_WIDTH, CARD_HEIGHT),
    "flop_2": (CARD_OFFSET_X, 0, CARD_WIDTH, CARD_HEIGHT),
    "flop_3": (CARD_OFFSET_X * 2, 0, CARD_WIDTH, CARD_HEIGHT),
    "turn": (CARD_OFFSET_X * 3.2, 0, CARD_WIDTH, CARD_HEIGHT), # Extra gap
    "river": (CARD_OFFSET_X * 4.2, 0, CARD_WIDTH, CARD_HEIGHT),
}

POT_GEOMETRY = {
    "pot": (0, 0, 150, 50)
}

SEAT_GEOMETRY = {
    "bet": (0, -50, 100, 40),
    "stack": (0, 100, 100, 40),
    "cards": (-65, -10, 130, 90),
    "name": (0, 150, 100, 40),
}

def make_rect_from_center(center_x: int, center_y: int, w: int, h: int) -> Rect:
    """Helper to create an (x, y, w, h) rect from a center point."""
    x = int(center_x - w / 2)
    y = int(center_y - h / 2)
    return (x, y, w, h)

class CalibrationWizard:
    def __init__(self, window_title: str):
        self.window_title = window_title
        self.capturer = WinDXGICapturer(target_window_title=window_title)
        self.click_points: List[Tuple[int, int]] = []
        self.current_step = 0
        self.window_name = "Calibration Wizard - Click prompts in terminal"

        self.steps = [
            "Click the CENTER of the FIRST FLOP card",
            "Click the CENTER of the POT",           
            "Click the CENTER of YOUR (Hero's) SEAT",
            "Click the CENTER of the SEAT TO HERO'S RIGHT",
            "Click the CENTER of the SEAT TO HERO'S LEFT",
            "Click the CENTER of the DEALER BUTTON",     
        ]

    def _mouse_callback(self, event: int, x: int, y: int, flags: int, param: Any):
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.current_step < len(self.steps):
                print(f"  > Click recorded at ({x}, {y})")
                self.click_points.append((x, y))
                self.current_step += 1
            else:
                print("All steps complete!")

    def run(self) -> None:
        try:
            with self.capturer as cap:
                cv2.namedWindow(self.window_name)
                cv2.setMouseCallback(self.window_name, self._mouse_callback)
                
                print("Starting calibration wizard. Please click on the OpenCV window.")
                
                while self.current_step < len(self.steps):
                    frame_data = cap.grab()
                    if not frame_data:
                        continue
                    
                    frame = frame_data.frame
                    
                    prompt = self.steps[self.current_step]
                    cv2.putText(frame, prompt, (50, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    
                    for i, (x, y) in enumerate(self.click_points):
                        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                        cv2.putText(frame, str(i), (x + 10, y + 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    cv2.imshow(self.window_name, frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("Calibration cancelled.")
                        return
                
                print("Calibration complete. Processing ROIs...")
                self.process_rois()

        except (RuntimeError, FileNotFoundError) as e:
            print(f"Error: {e}")
        finally:
            cv2.destroyAllWindows()

    def process_rois(self):
        if len(self.click_points) != len(self.steps):
            print("Error: Not enough click points. Aborting.")
            return

        board_anchor = self.click_points[0] 
        pot_anchor = self.click_points[1]    
        hero_anchor = self.click_points[2]
        right_anchor = self.click_points[3]
        left_anchor = self.click_points[4]
        dealer_anchor = self.click_points[5]

        board_rois = {}
        for name, (dx, dy, w, h) in BOARD_GEOMETRY.items():
            center_x = board_anchor[0] + dx
            center_y = board_anchor[1] + dy
            board_rois[name] = make_rect_from_center(center_x, center_y, w, h)
        
        pot_rect = make_rect_from_center(
            pot_anchor[0] + POT_GEOMETRY["pot"][0],
            pot_anchor[1] + POT_GEOMETRY["pot"][1],
            POT_GEOMETRY["pot"][2],
            POT_GEOMETRY["pot"][3]
        )
        board_rois["pot"] = pot_rect
        
        final_board = BoardROIs(**board_rois)

        final_dealer = DealerButtonROI(
            position_anchor=make_rect_from_center(dealer_anchor[0], dealer_anchor[1], 30, 30)
        )

        
        seat_anchors = {
            2: hero_anchor, 
            3: right_anchor,
            1: left_anchor,
        }
        
        final_seats: Dict[int, SeatROIs] = {}
        for seat_index, anchor in seat_anchors.items():
            seat_data = {"is_hero": (seat_index == 2)}
            for name, (dx, dy, w, h) in SEAT_GEOMETRY.items():
                center_x = anchor[0] + dx
                center_y = anchor[1] + dy
                seat_data[name] = make_rect_from_center(center_x, center_y, w, h)
            
            seat_data["seat_anchor"] = make_rect_from_center(anchor[0], anchor[1], 100, 100)
            final_seats[seat_index] = SeatROIs(**seat_data)

        profile_name = f"pokernow_{self.capturer.width}x{self.capturer.height}"
        resolution = (self.capturer.width, self.capturer.height)

        profile = RoiProfile(
            profile_name=profile_name,
            resolution=resolution,
            board=final_board,
            dealer_button=final_dealer,
            seats=final_seats
        )
        
        save_path = "data/roi_profile.json"
        # TODO: Ensure 'data/' directory exists
        profile.save_json(save_path)
        
        print(f"Success! ROI profile saved to {save_path}")
        print(profile.model_dump_json(indent=2))


def main():
    parser = argparse.ArgumentParser(description="ROI Calibration Wizard")
    parser.add_argument(
        "-t", "--title",
        type=str,
        default=None,
        help="Target window title. If not provided, a list will be shown."
    )
    args = parser.parse_args()
    
    title = args.title
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
            
    wizard = CalibrationWizard(window_title=title)
    wizard.run()

if __name__ == "__main__":
    main()