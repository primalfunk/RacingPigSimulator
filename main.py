from constants import CHARGING_MIN, CHARGING_MAX, TOTAL_TRACK_LENGTH, SPEED_MAX, SPEED_MIN, NORMAL, CHARGING, RECOVERING, STRAIGHTAWAY_LENGTH, TURN_LENGTH, WEATHER_CONDITIONS, TRACK_CONDITIONS, PIG_NAMES, AGILITY_MIN, AGILITY_MAX
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
        self.labels = [QLabel("") for _ in range(3)]  # Initialize three labels for the top three positions.
        for label in self.labels:
            self.layout.addWidget(label)
        
    def display_results(self, race_results):
        # Update results for the top three positions
        for i, result in enumerate(race_results[:3]):
            place = ["1st", "2nd", "3rd"][i]
            name = result['name']
            time = result['time']
            odds = result['odds']
            performance_level = result['performance_level']
            label_text = f"{place}: {name}, Time: {time:.2f} seconds, Odds: {odds:.2f}, Performance Level: {performance_level*100:.1f}"
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
        self.selected_pig = None
        self.betting_widget = self.race_track_widget.betting_widget
        self.betting_widget.pig_selected.connect(self.prepare_to_place_bet)
        self.betting_widget.bet_placed.connect(self.bet_has_been_placed)

    def init_ui(self):
        self.setWindowTitle("Racing Pig Simulator")
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
        self.start_button = QPushButton("Select a Racer")
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
            self.betting_widget.place_bet()
            self.start_button.setDisabled(True)
            self.race_controller.start_race()
        if self.start_button.text() == "Start Over":
            self.reset_race()

    def show_results(self):
        self.start_button.setDisabled(False)

    def closeEvent(self, event):
        self.race_track_widget.update_timer.stop()
        self.race_controller.clean_up()
        event.accept()

    def race_results_updated(self, name):
        pig = next((p for p in self.race_controller.pigs if p.name == name), None)
        if pig:
            self.race_results.append({
                'name': pig.name,
                'time': pig.time,
                'odds': pig.odds,
                'performance_level': pig.performance_level
            })
        else:
            print(f"Pig with name {name} not found.")

    def reset_race(self):
        self.start_button.setEnabled(True)
        self.start_button.setText("Select a Racer")
        self.race_recap_widget.hide()
        self.race_track_widget.show()
        self.race_results.clear()
        self.race_controller.clean_up() 
        self.race_track_widget.clear_pigs()
        self.race_controller = RaceController()
        for pig in self.race_controller.pigs:
            pig.finished.connect(self.race_track_widget.handle_pig_finished)
        self.race_controller.race_finished.connect(self.show_race_recap)
        self.display_pigs()

    def show_race_recap(self):
        # Sort the results by time
        sorted_results = sorted(self.race_results, key=lambda x: x['time'])
        self.race_recap_widget.display_results(sorted_results)
        self.race_recap_widget.show()
        self.start_button.setText("Start Over")
        self.start_button.setEnabled(True)

        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())