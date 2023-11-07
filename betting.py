from constants import PLAYER_START_BANK, DEFAULT_BET_SIZE
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer, Qt

class BettingWidget(QWidget):
    pig_selected = pyqtSignal()
    bet_placed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.racer_details_label = QLabel(self)
        self.racer_details_label.setTextFormat(Qt.RichText)
        self.racer_details_label.setWordWrap(True)
        self.racer_details_label.setMaximumHeight(100)
        self.player_start_bank = PLAYER_START_BANK
        self.bet_amount = DEFAULT_BET_SIZE
        self.init_ui() 

    def init_ui(self):
        self.setMinimumHeight(200)
        self.setMaximumHeight(400)
        layout = QVBoxLayout()
        upper_horizontal_line = QFrame()
        upper_horizontal_line.setFrameShape(QFrame.HLine)
        upper_horizontal_line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(upper_horizontal_line)
        layout.addWidget(self.racer_details_label)

        self.setLayout(layout)

    def show_racer_details(self, pig):
        details_html = f"""
        <html>
            <body>
                <h2>{pig.name}</h2>
                <p><b>Stats:</b> Top Speed: {pig.display_speed:.1f}, Agility: {pig.agility:.1f}, Endurance: {pig.endurance:.1f}, Vigor: {pig.vigor:.1f}, Spirit: {pig.spirit:.1f}, Energy: {pig.energy:.1f}, TPL: {pig.performance_level*100:.1f}%, Odds {pig.odds:.1f}</p>
            </body>
        </html>
        """
        self.racer_details_label.setText(details_html)
        self.pig_selected.emit()

    def clear_racer_details(self):
        self.racer_details_label.clear()

    def place_bet(self):
        self.bet_placed.emit()
        