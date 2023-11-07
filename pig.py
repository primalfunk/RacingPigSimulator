from betting import BettingWidget
from constants import SPEED_WEIGHT, ENDURANCE_WEIGHT, AGILITY_WEIGHT, ENERGY_WEIGHT, SPIRIT_WEIGHT, VIGOR_WEIGHT, ENERGY_MIN, ENERGY_MAX, END_MIN, END_MAX, VIG_MIN, VIG_MAX, CHARGING_MIN, CHARGING_MAX, TOTAL_TRACK_LENGTH, SPEED_MAX, SPEED_MIN, NORMAL, CHARGING, RECOVERING, STRAIGHTAWAY_LENGTH, TURN_LENGTH, WEATHER_CONDITIONS, TRACK_CONDITIONS, PIG_NAMES, AGILITY_MIN, AGILITY_MAX
from functools import partial
import logging
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QTimer
import random
import sys

class Pig(QObject):
    progress_updated = pyqtSignal(int)
    state_changed = pyqtSignal(str)
    finished = pyqtSignal(str, float)

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.is_selected = False
        self.distance_covered = 0.0
        self.running = False
        self.state = 'CHARGING'  # Current state of the pig: 'CHARGING', 'NORMAL', 'RECOVERING'
        self.state_timer = 0  # Timer to track how long we've been in the current state
        self.time = 0
        self.agility = random.uniform(AGILITY_MIN, AGILITY_MAX)
        self.top_speed = random.uniform(SPEED_MIN, SPEED_MAX)  # Top speed in km/h
        self.display_speed = self.top_speed
        self.endurance = random.uniform(END_MIN, END_MAX)  # Time in seconds the pig can maintain CHARGING, higher = better
        self.vigor = random.uniform(VIG_MIN, VIG_MAX)  # Time in seconds the pig is in RECOVERING, lower = better
        self.spirit = random.uniform(CHARGING_MIN, CHARGING_MAX)  # Chance to go into CHARGING state, higher = better
        self.energy = random.uniform(ENERGY_MIN, ENERGY_MAX) # Time in between charge checks, lower = better
        self.calculate_performance_level()
        self.odds = 0
        print(f"Racer name: {self.name} / SPD: {self.top_speed:.1f} / AGI: {self.agility:.1f} / END: {self.endurance:.1f} / VIG: {self.vigor:.1f} / SPI: {self.spirit:.1f} / ENE: {self.energy:.1f} / PER: {self.performance_level*100:.2f}")

    def run(self, weather_conditions, track_conditions):
        self.running = True
        charge_check_interval = self.energy * 100  # Check for charge according to the pig's stat
        charge_check_timer = 0  # Timer to track charge checks
        time_interval_ms = 100
        base_speed_mps = min(((self.top_speed * 1000) / 3600), 60)
        while self.running and self.distance_covered < TOTAL_TRACK_LENGTH:
            QThread.msleep(time_interval_ms)
            self.state_timer += time_interval_ms / 1000
            charge_check_timer += time_interval_ms
            if self.state == 'NORMAL' and charge_check_timer >= charge_check_interval:
                charge_check_timer = 0  # Reset timer
                if random.random() < self.spirit:
                    self.state = 'CHARGING'
                    self.state_timer = 0
                    self.state_changed.emit('CHARGING')  # Emit state change
            if self.state == 'CHARGING':
                if self.state_timer >= self.endurance:
                    self.state = 'RECOVERING'
                    self.state_timer = 0
                    self.state_changed.emit('RECOVERING')  # Emit state change
            elif self.state == 'RECOVERING' and self.state_timer >= self.vigor:
                self.state = 'NORMAL'
                self.state_timer = 0
                self.state_changed.emit('NORMAL')  # Emit state change
            speed_modifier = self.get_speed_modifier(weather_conditions, track_conditions)
            speed_multiplier = NORMAL
            if self.state == 'CHARGING':
                speed_multiplier = CHARGING
            elif self.state == 'RECOVERING':
                speed_multiplier = RECOVERING
            actual_speed_mps = base_speed_mps * speed_modifier * speed_multiplier
            self.distance_covered += actual_speed_mps * (time_interval_ms / 1000)
            self.progress_updated.emit(int((self.distance_covered / TOTAL_TRACK_LENGTH) * 100))
        finish_time = self.distance_covered / actual_speed_mps if actual_speed_mps != 0 else float('inf')
        print(f"Finish time for {self.name} is {finish_time:.2f}")
        self.time = finish_time
        self.finished.emit(self.name, finish_time)

    def get_speed_modifier(self, weather_conditions, track_conditions, is_turn=False):
        weather_impact = weather_conditions[1]
        track_impact = track_conditions[1]
        base_impact = (weather_impact + track_impact) / 2
        if is_turn:
            base_impact *= 5
        agility_factor = (self.agility - 50) / 50
        speed_modifier = max(1 - base_impact * (1 - agility_factor), 0.3)  # This ensures the modifier is never below 0.5
        return speed_modifier
    
    def stop(self):
        self.running = False

    def calculate_performance_level(self):
        normalized_speed = (self.top_speed - SPEED_MIN) / (SPEED_MAX - SPEED_MIN)
        normalized_agility = (self.agility - AGILITY_MIN) / (AGILITY_MAX - AGILITY_MIN)
        normalized_endurance = (self.endurance - END_MIN) / (END_MAX - END_MIN)
        normalized_vigor = (self.vigor - VIG_MIN) / (VIG_MAX - VIG_MIN)
        normalized_spirit = (self.spirit - CHARGING_MIN) / (CHARGING_MAX - CHARGING_MIN)
        normalized_energy = (self.energy - ENERGY_MIN) / (ENERGY_MAX - ENERGY_MIN)
        self.performance_level = (normalized_speed * SPEED_WEIGHT +
                                  normalized_agility * AGILITY_WEIGHT +
                                  normalized_endurance * ENDURANCE_WEIGHT +
                                  normalized_vigor * VIGOR_WEIGHT +
                                  normalized_spirit * SPIRIT_WEIGHT +
                                  normalized_energy * ENERGY_WEIGHT)
        