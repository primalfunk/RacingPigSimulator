from constants import DEFAULT_BET_SIZE
from PyQt5.QtWidgets import QComboBox, QWidget, QVBoxLayout, QFrame, QLabel, QHBoxLayout, QApplication
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer, Qt

class BettingWidget(QWidget):
    pig_selected = pyqtSignal()
    bet_placed = pyqtSignal((int, str))
    update_bet_amount = pyqtSignal(int)
    update_bet_type = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.racer_details_label = QLabel(self)
        self.racer_details_label.setTextFormat(Qt.RichText)
        self.racer_details_label.setWordWrap(True)
        self.racer_details_label.setMaximumHeight(100)
        self.bet_amount = DEFAULT_BET_SIZE
        self.bet_type = "Win"
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

            # Create a horizontal layout for dropdowns and label
            dropdown_layout = QHBoxLayout()

            # Label for bet selection
            self.bet_selection_label = QLabel("Select bet type and amount:")
            dropdown_layout.addWidget(self.bet_selection_label)

            # Dropdown menu for bet amount selection
            self.bet_amount_dropdown = QComboBox(self)
            self.bet_amount_dropdown.addItems(['5', '10', '25', '50'])  # Adding default bet amounts as strings
            self.bet_amount_dropdown.setCurrentIndex(1)  # Default selection index for '10'
            self.bet_amount_dropdown.currentIndexChanged.connect(self.bet_amount_changed)  # Connect signal to slot
            dropdown_layout.addWidget(self.bet_amount_dropdown)

            # Dropdown menu for bet type selection
            self.bet_type_dropdown = QComboBox(self)
            self.bet_type_dropdown.addItems(['Win', 'Place', 'Show'])  # Adding bet types
            self.bet_type_dropdown.currentIndexChanged.connect(self.bet_type_changed)  # Connect signal to slot
            dropdown_layout.addWidget(self.bet_type_dropdown)

            # Add the horizontal layout to the main vertical layout
            layout.addLayout(dropdown_layout)
            
            # Set the layout for the widget
            self.setLayout(layout)

    def show_racer_details(self, pig):
        details_html = f"""
        <html>
            <body>
                <h2>{pig.name}</h2>
                <p><b>Stats:</b> Top Speed: {pig.display_speed:.1f}, Agility: {pig.agility:.1f}, Endurance: {pig.endurance:.1f}, Vigor: {pig.vigor:.1f}, Spirit: {pig.spirit*100:.1f}, Energy: {pig.energy:.1f}, TPL: {pig.performance_level*100:.1f}%, Odds {pig.odds:.1f}</p>
            </body>
        </html>
        """
        self.racer_details_label.setText(details_html)
        self.pig_selected.emit()

    def clear_racer_details(self):
        self.racer_details_label.clear()

    def place_bet(self):
        selected_bet_amount = int(self.bet_amount_dropdown.currentText())  # Get the selected bet amount as integer
        selected_bet_type = str(self.bet_type_dropdown.currentText()) # Bet type as string
        self.bet_placed.emit(selected_bet_amount, selected_bet_type)  # Emit the selected bet amount and type
        QApplication.processEvents() # Try to hide the interface away immediately
        self.hide_betting_interface()

    def bet_amount_changed(self):
        self.bet_amount = int(self.bet_amount_dropdown.currentText())  # Update the bet_amount when selection changes
        self.update_bet_amount.emit(self.bet_amount) # Emit bet amount to the UI

    def bet_type_changed(self):
        # Update the bet_type when selection changes
        self.bet_type = str(self.bet_type_dropdown.currentText())
        self.update_bet_type.emit(self.bet_type) # Emit bet amount to the UI

    def hide_betting_interface(self):
        self.bet_selection_label.hide()
        self.bet_amount_dropdown.hide()
        self.bet_type_dropdown.hide()
        self.adjustSize() 
        