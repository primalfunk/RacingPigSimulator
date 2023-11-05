from constants import CHARGING_MIN, CHARGING_MAX, TOTAL_TRACK_LENGTH, SPEED_MAX, SPEED_MIN, NORMAL, CHARGING, RECOVERING, STRAIGHTAWAY_LENGTH, TURN_LENGTH, WEATHER_CONDITIONS, TRACK_CONDITIONS, PIG_NAMES, AGILITY_MIN, AGILITY_MAX
from functools import partial
import logging
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

# Configure logging at the root level of your application
logging.basicConfig(level=logging.DEBUG, filename='race_log.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('RacingPigSimulator')

class Pig(QObject):
    progress_updated = pyqtSignal(int)
    state_changed = pyqtSignal(str)  # New signal for state change
    finished = pyqtSignal(str, float)

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.top_speed = random.uniform(SPEED_MIN, SPEED_MAX)  # Top speed in km/h
        self.display_speed = self.top_speed
        self.agility = random.uniform(AGILITY_MIN, AGILITY_MAX)
        self.distance_covered = 0.0
        self.running = False
        self.state = 'NORMAL'  # Current state of the pig: 'CHARGING', 'NORMAL', 'RECOVERING'
        self.state_timer = 0  # Timer to track how long we've been in the current state
        self.endurance = random.uniform(3, 7)  # Time in seconds the pig can maintain CHARGING
        self.vigor = random.uniform(3, 7)  # Time in seconds the pig is in RECOVERING
        self.spirit = random.uniform(CHARGING_MIN, CHARGING_MAX)  # Chance to go into CHARGING state
        self.charging_counter = 0
        self.longest_charge_duration = 0
        self.current_charge_duration = 0

    def run(self, weather_conditions, track_conditions):
        self.running = True
        charge_check_interval = 10000  # Check for charge every 10 seconds
        charge_check_timer = 0  # Timer to track charge checks
        time_interval_ms = 100
        base_speed_mps = min(((self.top_speed * 1000) / 3600), 60)
        
        # Main running loop
        while self.running and self.distance_covered < TOTAL_TRACK_LENGTH:
            QThread.msleep(time_interval_ms)
            self.state_timer += time_interval_ms / 1000
            charge_check_timer += time_interval_ms
            # Check if it's time to try charging
            if self.state == 'NORMAL' and charge_check_timer >= charge_check_interval:
                charge_check_timer = 0  # Reset timer
                if random.random() < self.spirit:
                    self.state = 'CHARGING'
                    self.state_timer = 0
                    self.state_changed.emit('CHARGING')  # Emit state change
            # Handle state transitions
            if self.state == 'CHARGING':
                self.current_charge_duration += time_interval_ms / 1000
                self.charging_counter += 1
                if self.state_timer >= self.endurance:
                    self.state = 'RECOVERING'
                    self.state_timer = 0
                    self.state_changed.emit('RECOVERING')  # Emit state change
                    self.charging_counter += 1
                    if self.current_charge_duration > self.longest_charge_duration:
                        self.longest_charge_duration = self.current_charge_duration
                    self.current_charge_duration = 0
            elif self.state == 'RECOVERING' and self.state_timer >= self.vigor:
                self.state = 'NORMAL'
                self.state_timer = 0
                self.state_changed.emit('NORMAL')  # Emit state change
            # Calculate actual speed
            speed_modifier = self.get_speed_modifier(weather_conditions, track_conditions)
            speed_multiplier = NORMAL  # Default multiplier
            if self.state == 'CHARGING':
                speed_multiplier = CHARGING
            elif self.state == 'RECOVERING':
                speed_multiplier = RECOVERING
            actual_speed_mps = base_speed_mps * speed_modifier * speed_multiplier
            self.distance_covered += actual_speed_mps * (time_interval_ms / 1000)
            self.progress_updated.emit(int((self.distance_covered / TOTAL_TRACK_LENGTH) * 100))
        # Finalize race
        finish_time = self.distance_covered / actual_speed_mps if actual_speed_mps != 0 else float('inf')
        logger.info(f"Racer Pig {self.name} finished in {finish_time:.2f} seconds.")
        self.finished.emit(self.name, finish_time)

    def get_speed_modifier(self, weather_conditions, track_conditions, is_turn=False):
        weather_impact = weather_conditions[1]
        track_impact = track_conditions[1]
        base_impact = (weather_impact + track_impact) / 2
        if is_turn:
            base_impact *= 3
        agility_factor = (self.agility - 50) / 50
        speed_modifier = max(1 - base_impact * (1 - agility_factor), 0.5)  # This ensures the modifier is never below 0.5
        return speed_modifier
    
    def stop(self):
        self.running = False


class RaceController(QObject):
    race_finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        num_pigs = random.randint(5, 10)
        self.pigs = [Pig(name.replace(' ', '') + (str(random.randint(1, 9999)) if random.random() < 0.3 else '')) for name in random.sample(PIG_NAMES, num_pigs)]
        self.threads = []
        self.race_results = []
        self._race_started = False
        self._race_finished = False
        # Decide weather and track conditions
        weather_keys = list(WEATHER_CONDITIONS.keys())
        random_weather_key = random.choice(weather_keys)
        self.weather_condition = (random_weather_key, WEATHER_CONDITIONS[random_weather_key])
        # To select a random track condition
        track_keys = list(TRACK_CONDITIONS.keys())
        random_track_key = random.choice(track_keys)
        self.track_condition = (random_track_key, TRACK_CONDITIONS[random_track_key])

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
        # Store the results when a pig finishes
        logging.info(f"{name} finished in {time:.2f} seconds")
        self.race_results.append((name, time))
        # Only set the race as finished if all pigs have finished
        if all(not thread.isRunning() for thread in self.threads):
            self._race_finished = True
            self.race_finished.emit()

    def clean_up(self):
        for thread in self.threads:
            thread.quit()
            thread.wait()
        self.pigs.clear()
        self.threads.clear()
        self._race_started = False
        self._race_finished = False
        self.race_results.clear()


class RaceTrackWidget(QWidget):
    race_results_signal = pyqtSignal(str, float)

    def __init__(self, main_window, race_controller):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.pig_widgets = []
        self.init_timer()
        self.race_controller = race_controller
        self.first_pig_finished = False

    def init_ui(self):
        self.setMinimumWidth(800)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.weather_label = QLabel("Weather: ")
        self.track_label = QLabel("Track: ")
        self.layout.addWidget(self.weather_label)
        self.layout.addWidget(self.track_label)

    def init_timer(self):
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(100)  # 100 ms
        self.update_timer.timeout.connect(self.update_standings)
        self.update_timer.start()

    def add_pig(self, pig):
        progress_bar = QProgressBar()
        label_text = (f"*{pig.name}* Top Speed: {pig.display_speed:.2f} km/h, "
                      f"Agility: {pig.agility:.2f}, "
                      f"Endurance: {pig.endurance:.2f} s, "
                      f"Vigor: {pig.vigor:.2f} s, "
                      f"Spirit: {pig.spirit:.2f}, State: NORMAL")
        label = QLabel(label_text)
        progress_bar.setValue(0)

        pig.progress_updated.connect(progress_bar.setValue)
        pig.state_changed.connect(lambda state, pig=pig, label=label, progress_bar=progress_bar: self.update_pig_state_label(pig, label, progress_bar, state))
        
        self.pig_widgets.append((pig, label, progress_bar))
        self.layout.addWidget(label)
        self.layout.addWidget(progress_bar)

    def start_race_ui(self, weather_condition, track_condition):
        self.weather_label.setText(f"Weather: {weather_condition[0]}")
        self.track_label.setText(f"Track: {track_condition[0]}")

    def remove_pig(self, progress_bar, label):
        self.pig_widgets = [
            tup
            for tup in self.pig_widgets
            if tup[1] != label and tup[2] != progress_bar
        ]
        self.layout.removeWidget(progress_bar)
        self.layout.removeWidget(label)
        progress_bar.deleteLater()
        label.deleteLater()

    def clear_pigs(self):
        for pig, label, progress_bar in self.pig_widgets:
            self.layout.removeWidget(label)
            self.layout.removeWidget(progress_bar)
            label.deleteLater()
            progress_bar.deleteLater()
        self.pig_widgets.clear() 

    def update_standings(self):
        if self.race_controller._race_started and not self.race_controller._race_finished:
            self.pig_widgets.sort(key=lambda x: x[0].distance_covered, reverse=True)
            # Clear the current layout before re-adding widgets in the new order.
            for _, label, progress_bar in self.pig_widgets:
                self.layout.removeWidget(label)
                self.layout.removeWidget(progress_bar)
                label.hide()
                progress_bar.hide()
            # Re-add the widgets in the sorted order.
            for pig, label, progress_bar in self.pig_widgets:
                self.update_progress_bar_color(pig, progress_bar)
                self.layout.addWidget(label)
                self.layout.addWidget(progress_bar)
                label.show()
                progress_bar.show()

    def get_color_based_on_modifier(self, modifier):
        # Exponential scaling factors, these can be tweaked
        red_scaling_factor = 5
        green_scaling_factor = 5
        red_intensity = 255 * ((1 - modifier) ** red_scaling_factor)
        green_intensity = 255 * (modifier ** green_scaling_factor)
        red_intensity = max(0, min(255, red_intensity))
        green_intensity = max(0, min(255, green_intensity))
        blue_intensity = 0
        return f"rgb({int(red_intensity)}, {int(green_intensity)}, {int(blue_intensity)})"

    def update_pig_state_label(self, pig, label, progress_bar, state):
        # Update the label text to include the pig's current state
        label_text = (f"*{pig.name}* Top Speed: {pig.display_speed:.2f} km/h, "
                    f"Agility: {pig.agility:.2f}, "
                    f"Endurance: {pig.endurance:.2f} s, "
                    f"Vigor: {pig.vigor:.2f} s, "
                    f"Spirit: {pig.spirit:.2f}, State: {state}")
        label.setText(label_text)
        self.update_progress_bar_color(pig, progress_bar)
    
    def handle_pig_finished(self, name, time):
        self.first_pig_finished = True
        for pig, label, progress_bar in self.pig_widgets[:]:
            if pig.name == name:
                self.remove_pig(progress_bar, label)
                break
        self.race_results_signal.emit(name, time)
        if not any(pig.running for pig, _, _ in self.pig_widgets):
            self.race_controller._race_finished = True
            self.update_timer.stop()
            self.main_window.show_race_recap()

    def update_progress_bar_color(self, pig, progress_bar):
        if pig.state == "CHARGING":
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: lightblue; }")
        elif pig.state == "RECOVERING":
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        else:
            color = self.get_color_based_on_modifier(pig.get_speed_modifier(
                self.race_controller.weather_condition,
                self.race_controller.track_condition
            ))
            progress_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
            

class RaceRecapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.labels = []

    def display_results(self, race_results, pigs_info):
        # Clear existing results
        for label in self.labels:
            self.layout.removeWidget(label)
            label.deleteLater()
        self.labels.clear()
        self.layout.addWidget(QLabel("Race Recap: Top Three Positions"))
        for i, (name, time) in enumerate(race_results[:3]):
            place = ["1st", "2nd", "3rd"][i]
            # Find additional info for each pig
            pig_charging_info = pigs_info.get(name, {})
            charges = pig_charging_info.get('charging_counter', 0)
            longest_charge = pig_charging_info.get('longest_charge_duration', 0)
            label = QLabel(f"{place}: {name}, Time: {time:.2f} seconds, Charges: {charges}, Longest Charge: {longest_charge:.2f} seconds")
            self.labels.append(label)
            self.layout.addWidget(label)


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

    def init_ui(self):
        self.setWindowTitle("Racing Pig Simulator")
        self.setGeometry(200, 200, 900, 300)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.race_track_widget = RaceTrackWidget(self, self.race_controller)
        # Update the UI with the current conditions
        self.race_track_widget.start_race_ui(
                self.race_controller.weather_condition, 
                self.race_controller.track_condition
                )
        self.layout.addWidget(self.race_track_widget)
        self.start_button = QPushButton("Start Race")
        self.start_button.clicked.connect(self.start_race)
        self.layout.addWidget(self.start_button)
        self.central_widget.setLayout(self.layout)

    def display_pigs(self):
        for pig in self.race_controller.pigs:
            self.race_track_widget.add_pig(pig)

    def start_race(self):
        if self.start_button.text() == "Start Over":
            self.reset_race()
        else:
            self.start_button.setDisabled(True)
            logging.info("Race is starting.")
            self.race_controller.start_race()

    def show_results(self):
        print("Race finished")
        self.start_button.setDisabled(False)

    def closeEvent(self, event):
        self.race_track_widget.update_timer.stop()
        self.race_controller.clean_up()
        event.accept()

    def race_results_updated(self, name, time):
        self.race_results.append((name, time))

    def reset_race(self):
        self.start_button.setEnabled(True)
        self.start_button.setText("Start Race")
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
        pigs_info = {pig.name: {'charging_counter': pig.charging_counter,
                        'longest_charge_duration': pig.longest_charge_duration}
             for pig in self.race_controller.pigs}
        sorted_results = sorted(self.race_results, key=lambda x: x[1])
        self.race_recap_widget.display_results(sorted_results, pigs_info)
        self.race_recap_widget.show()
        self.start_button.setText("Start Over")
        self.start_button.setEnabled(True)
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())