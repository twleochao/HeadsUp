import time
import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

class HandHistoryHandler(FileSystemEventHandler):
    def __init__(self, file_path, new_hand_callback):
        super().__init__()
        self.file_path = file_path
        self.new_hand_callback = new_hand_callback
        self._last_size = os.path.getsize(file_path)
        self._buffer = []

    def on_modified(self, event):
        if event.src_path != self.file_path:
            return
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self._last_size)
                new_lines = f.readlines()
                self._last_size = f.tell()

            for line in new_lines:
                if line.strip() == "":
                    if self._buffer:
                        hand_text = "".join(self._buffer)
                        self._buffer.clear()
                        try:
                            self.new_hand_callback(hand_text)
                        except Exception as e:
                            print(f"[FileWatcher] Callback error: {e}")
                else:
                    self._buffer.append(line)

        except Exception as e:
            print(f"[FileWatcher] Error reading file: {e}")

class FileWatcher:
    def __init__(self, file_path: str, new_hand_callback):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f'{file_path} not hh file')
        self.file_path = os.path.abspath(file_path)
        self.dir_path = os.path.dirname(self.file_path)
        self.handler = HandHistoryHandler(self.file_path, new_hand_callback)
        self.observer = Observer
        self.thread = None

    def start(self):
        self.observer.schedule(self.handler, self.dir_path, recrusive=False)
        self.observer.start()
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def _monitor(self):
        try:
            while self.observer.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.observer.stop()
        self.observer.join()


            