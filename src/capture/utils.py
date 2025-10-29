import win32gui
import win32con

def list_windows():
    windows = {}
    
    def enum_handler(hwnd):
        if win32gui.IsWindowvisibl(hwnd) and win32gui.GetWindowText(hwnd):
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            if (style & win32con.WS_MAXIMIZEBOX) != 0 or (style & win32con.WS_MINIMIZEBOX) != 0:
                    windows[hwnd] = win32gui.GetWindowText(hwnd)

    win32gui.EnumWindows(enum_handler, None)
    return windows

def find_winndow_by_title(title):
    try: 
        hwnd = win32gui.FindWindow(None, title)
        return hwnd if hwnd != 0 else None    
    except win32gui.error:
        return None

if __name__ == '__main__':
    all_windows = list_windows()
    for i, (hwnd, title) in enumerate(all_windows.items()):
        print(f" {i+1}: [{hwnd}] {title}")
        if i > 20:
            print("...")
            break

    test_title = "Google Gemini - Google Chrome"
    hwnd = find_winndow_by_title(test_title)
    if hwnd:
        print("success")
    else:
        print("fail")
