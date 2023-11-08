from constants import PLAYER_START_BANK, DEFAULT_BET_SIZE, CHARGING_MIN, CHARGING_MAX, TOTAL_TRACK_LENGTH, SPEED_MAX, SPEED_MIN, NORMAL, CHARGING, RECOVERING, STRAIGHTAWAY_LENGTH, TURN_LENGTH, WEATHER_CONDITIONS, TRACK_CONDITIONS, PIG_NAMES, AGILITY_MIN, AGILITY_MAX
from functools import partial
import logging
from pig import Pig
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar )
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
from race_controller import RaceController
from racetrack import RaceTrackWidget
import random
import sys

class RaceRecapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.recap_label = QLabel("Race Recap: Top Three Positions")
        self.layout.addWidget(self.recap_label)
        self.labels = [QLabel("") for _ in range(3)]
        for label in self.labels:
            self.layout.addWidget(label)
        
    def display_results(self, race_results):
        # Update results for the top three positions
        for i, result in enumerate(race_results[:3]):
            place = ["1st", "2nd", "3rd"][i]
            name = result['Racer Pig']
            time = result['Finishing Time']
            odds = result['Win Odds']
            performance_level = result['Performance Rating']
            label_text = f"{place}: Racing Pig {name}, Finishing Time: {time:.2f} seconds, Win Odds: {odds:.2f}, Performance Level: {performance_level*100:.1f}"
            self.labels[i].setText(label_text)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.race_controller = RaceController()
        self.race_controller.race_finished.connect(self.show_race_recap)
        self.race_results = []
        self.init_ui()
        self.display_pigs()
        self.race_recap_widget = RaceRecapWidget()
        self.race_track_widget.race_results_signal.connect(self.race_results_updated)
        for pig in self.race_controller.pigs:
            pig.finished.connect(self.race_track_widget.handle_pig_finished)
        self.layout.addWidget(self.race_recap_widget)
        self.race_recap_widget.hide()
        self.betting_widget = self.race_track_widget.betting_widget
        self.betting_widget.pig_selected.connect(self.prepare_to_place_bet)
        self.betting_widget.bet_placed.connect(self.bet_has_been_placed)

    def init_ui(self):
        self.setWindowTitle("Realistic Racing Pig Simulator")
        self.setGeometry(200, 200, 900, 300)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.race_track_widget = RaceTrackWidget(self, self.race_controller)
        self.race_track_widget.start_race_ui(
                self.race_controller.weather_condition, 
                self.race_controller.track_condition
                )
        self.layout.addWidget(self.race_track_widget)
        self.start_button = QPushButton("Select Racer and Place Bet")
        # The click of the so-called Start Button is here connected to the function which emits the race-starting logic
        self.start_button.clicked.connect(self.handle_start_button)
        self.layout.addWidget(self.start_button)
        self.central_widget.setLayout(self.layout)

    def display_pigs(self):
        
        for pig in self.race_controller.pigs:
            self.race_track_widget.add_pig(pig)
        self.race_track_widget.calculate_odds()

    def prepare_to_place_bet(self):
        self.start_button.setText("Place Bet")

    def bet_has_been_placed(self):
        self.start_button.setText("RACE IN PROGRESS")

    def handle_start_button(self):
        if self.start_button.text() == "Place Bet":
            if self.race_track_widget.selected_pig_widget is not None:
                # This method in the other class emits the "bet_placed" signal from the BettingWidget
                self.betting_widget.place_bet()
                self.start_button.setDisabled(True)
                self.betting_widget.bet_amount_dropdown.setDisabled(True)
                self.betting_widget.bet_type_dropdown.setDisabled(True)
                self.race_controller.start_race()
        if self.start_button.text() == "Race Again":
            self.reset_race(False)

    def show_results(self):
        self.start_button.setEnabled(True)
        self.betting_widget.bet_amount_dropdown.setEnabled(True)

    def closeEvent(self, event):
        self.race_track_widget.update_timer.stop()
        self.race_controller.clean_up()
        event.accept()

    def race_results_updated(self, name):
        pig = next((p for p in self.race_controller.pigs if p.name == name), None)
        if pig:
            self.race_results.append({'Racer Pig': pig.name, 'Finishing Time': pig.time, 'Win Odds': pig.odds, 'Performance Rating': pig.performance_level})
        else:
            print(f"Pig with name {name} not found.")

    def reset_race(self, new = False):
        if new:
            self.race_track_widget.bank = PLAYER_START_BANK
        # Check if there's enough in the bank to place any bets (if not, game over message)
        self.race_track_widget.check_bank_status()
        self.betting_widget.bet_amount = DEFAULT_BET_SIZE
        self.start_button.setEnabled(True)
        self.betting_widget.clear_racer_details()
        self.betting_widget.bet_amount_dropdown.setEnabled(True)
        self.betting_widget.bet_type_dropdown.setEnabled(True)
        self.start_button.setText("Select a Racer Pig")
        self.race_recap_widget.hide()
        self.race_track_widget.show()
        self.race_results.clear()
        self.race_controller.clean_up() 
        self.race_track_widget.selected_pig_widget = None
        self.race_track_widget.clear_pigs()
        # Reset the counter for the Win/Place/Show logic
        self.race_track_widget.finished_place = 1
        # Reset the Race Controller
        self.race_controller = RaceController()
        # Reconnect the origin for the finishing signal for each pig, to run the placing logic in RaceTrackWidget
        for pig in self.race_controller.pigs:
            pig.finished.connect(self.race_track_widget.handle_pig_finished)
            print(f"Reconnected pig {pig.name} to the finish line proc")
        # Reconnect the origin for the race finish, to show the race recap
        self.race_controller.race_finished.connect(self.show_race_recap)
        self.display_pigs()
        # Reset the timer for updating standings and pig finish times
        self.race_track_widget.reset_timer()
        self.betting_widget.show()
        self.betting_widget.update_bet_amount_options(self.race_track_widget.bank)

    def show_race_recap(self):
        sorted_results = sorted(self.race_results, key=lambda x: x['Finishing Time'])
        self.race_recap_widget.display_results(sorted_results)
        self.race_recap_widget.show()
        self.start_button.setText("Race Again")
        self.start_button.setEnabled(True)

        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())