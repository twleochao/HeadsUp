import time
from PySide6.QtCore import QObject, Signal, Slot
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from PokerNow import PokerClient

class PokerPoller(QObject):
    game_pot_updated = Signal(str) 

    # game_state_updated = Signal(object)
    
    def __init__(self, game_url: str):
        super().__init__()
        self.game_url = game_url
        self._is_running = True
        self.client: PokerClient = None
        self.driver: webdriver.Chrome = None

    @Slot()
    def run(self):
        try:
            self.driver = webdriver.Chrome()
            self.client = PokerClient(self.driver)
            
            print(f"Navigating to {self.game_url}...")
            self.client.navigate(self.game_url)
            
            print("\n" + "="*30)
            print("ACTION REQUIRED:")
            print("1. In the Chrome window, log in and/or join the game.")
            print("2. Sit at the table.")
            print("="*30)
            input("\nPress Enter in this console *after* you are sitting at the table...")
            print("--- Polling started. (Press Ctrl+C in console to quit) ---")

            while self._is_running:
                try:
                    state = self.client.game_state_manager.get_game_state()
                    self.game_pot_updated.emit(state.pot_size)
                    
                    # self.game_state_updated.emit(state)

                except Exception as e:
                    print(f"Error fetching game state: {e}")
                
                time.sleep(2)

        except WebDriverException as e:
            print(f"WebDriver Error: {e}")
            if "chromedriver" in str(e):
                print("FIX: Ensure 'chromedriver.exe' is in your system PATH or download the correct version.")
        except Exception as e:
            print(f"Unhandled error in polling thread: {e}")
        finally:
            if self.driver:
                self.driver.quit()
            print("Polling service stopped.")

    def stop(self):
        self._is_running = False