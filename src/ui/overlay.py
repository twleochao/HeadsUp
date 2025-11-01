import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
)
from PySide6.QtCore import Qt, Slot, QSize

class HudOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0.5); border-radius: 10px;")
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.pot_label = QLabel("Pot: N/A")
        self.pot_label.setStyleSheet("color: white; font-size: 16px; padding: 10px;")
        self.layout.addWidget(self.pot_label)

        self.board_label = QLabel("Board: ---")  # <-- NEW
        self.board_label.setStyleSheet("color: white; font-size: 16px; padding: 5px 10px;")
        self.layout.addWidget(self.board_label)

        self.hero_cards_label = QLabel("Hero: ---")  # <-- NEW
        self.hero_cards_label.setStyleSheet("color: #FFFF00; font-size: 16px; padding: 5px 10px;")
        self.layout.addWidget(self.hero_cards_label)
        
        self.action_label = QLabel("Action: ---")
        self.action_label.setStyleSheet("color: #00FF00; font-size: 18px; font-weight: bold; padding: 10px;")
        self.layout.addWidget(self.action_label)

        self.setGeometry(50, 50, 300, 150) # x, y, w, h

    @Slot(str)
    def update_pot_display(self, pot_str: str):
        """Public slot to update the pot label from the polling thread."""
        if pot_str:
            self.pot_label.setText(f"Pot: {pot_str}")
        else:
            self.pot_label.setText("Pot: 0")

    @Slot(str)
    def update_board_display(self, board_str: str): 
        """Public slot to update the board label."""
        self.board_label.setText(f"Board: {board_str}")

    @Slot(str)
    def update_hero_cards_display(self, cards_str: str):
        """Public slot to update the hero cards label."""
        self.hero_cards_label.setText(f"Hero: {cards_str}")

    @Slot(str)
    def update_action_display(self, action_str: str):
        """Public slot to update the action label."""
        self.action_label.setText(f"Action: {action_str}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = HudOverlay()
    overlay.show()
    
    def test_update():
        overlay.update_pot_display("100.5 BB")
        overlay.update_action_display("RAISE 3bb")
    
    from PySide6.QtCore import QTimer
    QTimer.singleShot(2000, test_update)
    
    sys.exit(app.exec())