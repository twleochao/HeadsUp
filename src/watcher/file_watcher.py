import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

class HandHistoryHandler(FileSystemEventHandler):
    def __init__(self, on_new_hand, file_filter=None):
        self.on_new_hand = on_new_hand
        self.file_filter = file_filter or(lambda f: f.endswith('.txt'))
        self.last_processed = {}

    def on_modified(self, event):
        if event.is_directory:
            return
    
        file_path = Path(event.src_path)

        if not self.file_filter(str(file_path)):
            return

        previous_size = self.last_processed.get(str(file_path), 0)
        current_size = file_path.stat().st_size

        if current_size <= previous_size:
            return
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(previous_size)
            new_data = f.read()
            self.last_processed[str(file_path)] = current_size

            if "*** SUMMARY ***" in new_data:
                self.on_new_hand(file_path, new_data)

def start_watching(folder_path: str, on_new_hand):
    path = Path(folder_path).expanduser()
    if not path.exists():
        raise FileNotFoundError()
    
    event_handler = HandHistoryHandler(on_new_hand)
    observer = Observer
    observer.schedule(event_handler, str(path), recursive=True)
    observer.start
    print('watching start')
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

            