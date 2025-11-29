import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Signal
from src.ui.overlay import HudOverlay
from src.services.polling_service import PokerPoller
from src.core.state_manager import AppStateManager
from src.services.data_logger import DataLogger

POKER_NOW_GAME_URL = "https://www.pokernow.club/games/..." 
POKER_NOW_GAME_URL = "https://www.pokernow.club/games/pglOvxyJtpu4VvmX8J8sC_LIr"

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

logger_thread = QThread()
logger_worker = DataLogger()
logger_worker.moveToThread(logger_thread)

poller_thread.started.connect(poller_worker.run)
poller_thread.finished.connect(poller_worker.stop)

poller_worker.game_state_updated.connect(state_manager.update_raw_game_state)

state_manager.ui_pot_updated.connect(hud.update_pot_display)
state_manager.ui_board_updated.connect(hud.update_board_display)
state_manager.ui_hero_cards_updated.connect(hud.update_hero_cards_display)
state_manager.ui_hero_position_updated.connect(hud.update_hero_position_display)
state_manager.ui_turn_updated.connect(hud.update_turn_display)
state_manager.ui_action_updated.connect(hud.update_action_display)

state_manager.log_decision_made.connect(logger_worker.log_decision)

logger_thread.start()
app.aboutToQuit.connect(logger_thread.quit)

poller_thread.start()

hud.show()
sys.exit(app.exec())