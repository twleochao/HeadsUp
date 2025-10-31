import cv2
import time
import argparse
from typing import Type
from src.capture.base_capturer import BaseCapturer
from src.capture.win_dxgi_capturer import WinDXGICapturer
from src.capture.utils import list_windows

CAPTURE_METHODS = {
    "dxgi": WinDXGICapturer,
}

def main(method: str, title: str):
    
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

    print(f"Attempting to capture '{title}' using {method}...")

    CapturerClass: Type[BaseCapturer] = CAPTURE_METHODS.get(method)
    if not CapturerClass:
        print(f"Error: Unknown capture method '{method}'")
        return

    try:
        with CapturerClass(target_window_title=title) as capturer:
            print(f"Capture started. Press 'q' to quit.")
            
            frame_count = 0
            start_time = time.perf_counter()
            
            while True:
                frame_data = capturer.grab()
                
                if frame_data:
                    frame = frame_data.frame
                    frame_count += 1
                    
                    now = time.perf_counter()
                    elapsed = now - start_time
                    
                    if elapsed > 0:
                        fps = frame_count / elapsed
                        
                    cv2.putText(
                        frame,
                        f"FPS: {fps:.2f}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                    )
                    cv2.putText(
                        frame,
                        f"Latency: {frame_data.capture_latency_ms:.2f} ms",
                         (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                    )
                    cv2.putText(
                        frame,
                        f"Method: {method}",
                         (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                    )

                    cv2.imshow("Capture Test", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
                time.sleep(0.001) 

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Error: {e}")
    finally:
        cv2.destroyAllWindows()
        print("Test finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test window capture methods.")
    parser.add_argument(
        "-m", "--method", 
        type=str, 
        choices=CAPTURE_METHODS.keys(), 
        default="dxgi",
        help="Capture method to use."
    )
    parser.add_argument(
        "-t", "--title",
        type=str,
        default=None,
        help="Target window title. If not provided, a list will be shown."
    )
    args = parser.parse_args()
    
    main(args.method, args.title)