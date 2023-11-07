from betting import BettingWidget
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
import random
import sys

class RaceController(QObject):
    race_finished = pyqtSignal()
    update_race_recap_signal = pyqtSignal(list)
    def __init__(self):
        super().__init__()
        num_pigs = random.randint(5, 10)
        self.pigs = [Pig(name.replace(' ', '') + (str(random.randint(1, 9999)) if random.random() < 0.03 else '')) for name in random.sample(PIG_NAMES, num_pigs)]
        self.threads = []
        self.race_results = []
        self._race_started = False
        self._race_finished = False

        weather_weights = self.generate_weights(len(WEATHER_CONDITIONS))
        track_weights = self.generate_weights(len(TRACK_CONDITIONS))
        random_weather_key = self.weighted_choice(WEATHER_CONDITIONS, weather_weights)
        random_track_key = self.weighted_choice(TRACK_CONDITIONS, track_weights)
        self.weather_condition = (random_weather_key, WEATHER_CONDITIONS[random_weather_key])
        self.track_condition = (random_track_key, TRACK_CONDITIONS[random_track_key])
        print("Selected Weather Condition:", self.weather_condition)
        print("Selected Track Condition:", self.track_condition)

    def weighted_choice(self, options, weights):
        keys = list(options.keys())
        return random.choices(keys, weights=weights, k=1)[0]
    
    def generate_weights(self, num_items):
        return [0.9 - (i * (0.6 / (num_items - 1))) for i in range(num_items)]
    
    def start_race(self):
        self._race_started = True
        logging.info(f"Race started with weather: {self.weather_condition[0]} and track: {self.track_condition[0]}")
        for pig in self.pigs:
            pig_thread = QThread()
            pig.moveToThread(pig_thread)
            pig_thread.started.connect(partial(pig.run, self.weather_condition, self.track_condition))
            pig.finished.connect(self.check_finish)
            pig.finished.connect(pig_thread.quit)
            self.threads.append(pig_thread)
            pig_thread.start()

    def check_finish(self, name, time):
        # Find the pig object by name
        pig = next((p for p in self.pigs if p.name == name), None)
        if pig:
            logging.info(f"{name} finished in {time:.2f} seconds")
            if len(self.race_results) < 3:
                self.race_results.append(pig)
                self.update_race_recap_signal.emit(self.race_results)
                if all(pig.time is not None for pig in self.pigs):
                    self._race_finished = True
                    self.race_finished.emit()
        else:
            logging.error(f"Pig with name {name} not found.")

    def clean_up(self):
        for thread in self.threads:
            thread.quit()
            thread.wait()
        self.pigs.clear()
        self.threads.clear()
        self._race_started = False
        self._race_finished = False
        self.race_results.clear()
