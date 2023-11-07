from betting import BettingWidget
from constants import ODDS_MIN, ODDS_MAX
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QFrame )
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QFont

class ClickableLabel(QLabel):
    clicked = pyqtSignal(object)  # Signal to emit the pig object

    def __init__(self, pig, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pig = pig  # Store a reference to the pig
        self.setText(self.pig.name)
        self.setMouseTracking(True)
        self.setStyleSheet("QLabel { border: 2px solid transparent; }")

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.clicked.emit(self.pig)


class RaceTrackWidget(QWidget):
    race_results_signal = pyqtSignal(str, float)

    def __init__(self, main_window, race_controller):
        super().__init__()
        self.selected_pig_widget = None
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
        race_details_label = QLabel("RACE DETAILS")
        bold_font = QFont()
        bold_font.setBold(True)
        race_details_label.setFont(bold_font)
        race_details_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(race_details_label)
        upper_horizontal_line = QFrame()
        upper_horizontal_line.setFrameShape(QFrame.HLine)
        upper_horizontal_line.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(upper_horizontal_line)
        labels_layout = QHBoxLayout()
        self.weather_label = QLabel("Weather Conditions: ")
        self.track_label = QLabel("Track Conditions: ")
        labels_layout.addWidget(self.weather_label)
        labels_layout.addWidget(self.track_label)
        self.layout.addLayout(labels_layout)
        lower_horizontal_line = QFrame()
        lower_horizontal_line.setFrameShape(QFrame.HLine)
        lower_horizontal_line.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(lower_horizontal_line)
        self.pigs_layout = QVBoxLayout()
        self.layout.addLayout(self.pigs_layout)
        self.betting_widget = BettingWidget(self)
        self.layout.addWidget(self.betting_widget)

    def init_timer(self):
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(100)  # 100 ms
        self.update_timer.timeout.connect(self.update_standings)
        self.update_timer.start()

    def add_pig(self, pig):
        progress_bar = QProgressBar()
        label_text = f"Name:{pig.name} PRF: {pig.performance_level} Odds: {pig.odds:.2f}  State: READY"
        pig.label = ClickableLabel(pig)
        pig.label.clicked.connect(lambda pig=pig: self.update_racer_details(pig))
        pig.label.setText(label_text)
        pig.label.setMouseTracking(True)
        pig.label.setStyleSheet("QLabel { border: 2px solid transparent; }")
        progress_bar.setValue(0)
        pig.progress_updated.connect(progress_bar.setValue)
        pig.state_changed.connect(lambda state, pig=pig, label=pig.label, progress_bar=progress_bar: self.update_pig_state_label(pig, label, progress_bar, state))
        pig.label.clicked.connect(self.update_racer_details)
        self.pig_widgets.append((pig, pig.label, progress_bar))
        self.pigs_layout.addWidget(pig.label)
        self.pigs_layout.addWidget(progress_bar)

    def start_race_ui(self, weather_condition, track_condition):
        self.weather_label.setText(f"Weather Conditions: {weather_condition[0]}")
        self.track_label.setText(f"Track Conditions: {track_condition[0]}")

    def calculate_odds(self):
        # First, determine the range of performance levels among all pigs
        min_per = min(pig.performance_level for pig, _, _ in self.pig_widgets)
        max_per = max(pig.performance_level for pig, _, _ in self.pig_widgets)
        for pig, label, _ in self.pig_widgets:
            normalized_per = (pig.performance_level - min_per) / (max_per - min_per) if max_per != min_per else 1
            odds = ((1 - normalized_per) * (ODDS_MAX - ODDS_MIN)) + ODDS_MIN
            pig.odds = max(min(odds, ODDS_MAX), ODDS_MIN)
            print(f"{pig.name} odds calculated as {pig.odds:.2f} with PER of {pig.performance_level*100:.1f}")
            self.update_pig_state_label(pig, label, None, pig.state)
    
    def remove_pig(self, progress_bar, label):
        self.pig_widgets = [
            tup
            for tup in self.pig_widgets
            if tup[1] != label and tup[2] != progress_bar
        ]
        self.pigs_layout.removeWidget(progress_bar)
        self.pigs_layout.removeWidget(label)
        progress_bar.deleteLater()
        label.deleteLater()

    def clear_pigs(self):
        for pig, label, progress_bar in self.pig_widgets:
            self.pigs_layout.removeWidget(label)
            self.pigs_layout.removeWidget(progress_bar)
            label.deleteLater()
            progress_bar.deleteLater()
        self.pig_widgets.clear() 

    def update_racer_details(self, pig):
            # Prevent selection if the race has started
            if self.race_controller._race_started:
                return
            if self.selected_pig_widget:
                self.selected_pig_widget.label.setStyleSheet("QLabel { border: 2px solid transparent; }")
                self.betting_widget.clear_racer_details()  # Clear previous details
            self.selected_pig_widget = pig
            pig.label.setStyleSheet("QLabel { border: 1px solid blue; }")
            self.betting_widget.show_racer_details(pig)  # Show the details of the selected pig
            for pig_widget, label, _ in self.pig_widgets:
                if pig_widget is pig:
                    label.setText(f"{pig.name} PER:{pig.performance_level*100:.1f} Odds:{pig.odds:.1f}")
                else:
                    label.setText(f"{pig_widget.name} PER:{pig_widget.performance_level*100:.1f} Odds:{pig_widget.odds:.1f}")

    def update_standings(self):
        if self.race_controller._race_started and not self.race_controller._race_finished:
            self.pig_widgets.sort(key=lambda x: x[0].distance_covered, reverse=True)
            # Clear the current layout before re-adding widgets in the new order.
            for _, label, progress_bar in self.pig_widgets:
                self.pigs_layout.removeWidget(label)
                self.pigs_layout.removeWidget(progress_bar)
                label.hide()
                progress_bar.hide()
            # Re-add the widgets in the sorted order.
            for pig, label, progress_bar in self.pig_widgets:
                self.update_progress_bar_color(pig, progress_bar)
                self.pigs_layout.addWidget(label)
                self.pigs_layout.addWidget(progress_bar)
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
        label_text = f"Name:{pig.name} PRF: {pig.performance_level:.1f} Odds: {pig.odds:.2f}  State:{state}"
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
        if progress_bar is not None:
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