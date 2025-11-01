import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Signal
from src.ui.overlay import HudOverlay
from src.services.polling_service import PokerPoller
from src.core.state_manager import AppStateManager

POKER_NOW_GAME_URL = "https://www.pokernow.club/games/..." 
#POKER_NOW_GAME_URL = ""

if POKER_NOW_GAME_URL == "https://www.pokernow.club/games/...":
    print("="*50)
    POKER_NOW_GAME_URL = input("Enter PokerNow Gamelink: ")
    print("="*50)

app = QApplication(sys.argv)

hud = HudOverlay()
state_manager = AppStateManager()

poller_thread = QThread()
poller_worker = PokerPoller(POKER_NOW_GAME_URL)
poller_worker.moveToThread(poller_thread)
poller_thread.started.connect(poller_worker.run)
poller_thread.finished.connect(poller_worker.stop)
poller_worker.game_pot_updated.connect(hud.update_pot_display)
poller_worker.game_state_updated.connect(state_manager.update_raw_game_state)
poller_thread.start()

hud.show()
sys.exit(app.exec())