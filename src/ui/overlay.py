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

        self.board_label = QLabel("Board: ---") 
        self.board_label.setStyleSheet("color: white; font-size: 16px; padding: 5px 10px;")
        self.layout.addWidget(self.board_label)

        self.hero_cards_label = QLabel("Hero: ---")
        self.hero_cards_label.setStyleSheet("color: #FFFF00; font-size: 16px; padding: 5px 10px;")
        self.layout.addWidget(self.hero_cards_label)

        self.hero_pos_label = QLabel("Pos: ---")
        self.hero_pos_label.setStyleSheet("color: #FFFF00; font-size: 16px; padding: 5px 10px;")
        self.layout.addWidget(self.hero_pos_label)

        self.turn_label = QLabel("Turn: ---")
        self.turn_label.setStyleSheet("color: #FF8C00; font-size: 16px; padding: 5px 10px;")
        self.layout.addWidget(self.turn_label)
        
        self.action_label = QLabel("Action: ---")
        self.action_label.setStyleSheet("color: #00FF00; font-size: 18px; font-weight: bold; padding: 10px;")
        self.layout.addWidget(self.action_label)

        self.setGeometry(50, 50, 300, 280)

    @Slot(str)
    def update_pot_display(self, pot_str: str):
        if pot_str:
            self.pot_label.setText(f"Pot: {pot_str}")
        else:
            self.pot_label.setText("Pot: 0")

    @Slot(str)
    def update_board_display(self, board_str: str): 
        self.board_label.setText(f"Board: {board_str}")

    @Slot(str)
    def update_hero_cards_display(self, cards_str: str):
        self.hero_cards_label.setText(f"Hero: {cards_str}")

    @Slot(str)
    def update_hero_position_display(self, pos_str: str):
        self.hero_pos_label.setText(f"Pos: {pos_str}")

    @Slot(str)
    def update_turn_display(self, player_name: str):
        self.turn_label.setText(f"Turn: {player_name}")

    @Slot(str)
    def update_action_display(self, action_str: str):
        self.action_label.setText(f"Action: {action_str}")