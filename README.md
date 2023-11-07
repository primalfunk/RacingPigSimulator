# Racing Pig Simulator

This project is a whimsical and entertaining racing simulator that answers the age old question - what if we had a horse racing simulator, but instead of horses, pigs? It showcases the use of threads, signals, and slots in PyQt5, demonstrating how these elements can be employed to create a dynamic and interactive application. The simulator includes intricate mechanics such as calculating statistics and odds for a set of randomly generated pig racers, providing users with a unique experience each race.

The current updates are around implementing the betting system to create a simple game loop.

## Overview

The Racing Pig Simulator consists of the following components:

- `main.py` - Initializes the main window UI and orchestrates the connections between the various parts of the program's logic.
- `race_controller.py` - Oversees the race mechanics, including initiating threads for each pig, monitoring race progress, and terminating threads post-race.
- `pig.py` - Defines the `Pig` class, which embodies the attributes and behaviors of a racing pig, including its statistics and racing logic.
- `racetrack.py` - Houses the animated racetrack widget and its associated betting interface.
- `betting.py` - Contains the logic for the betting interface.
- `constants.py` - Stores constants utilized across the project for easy maintenance and updates.

## Pig Stats

Each instance of `Pig` generates the following statistics randomly:

- **Top Speed**: Maximum velocity of the pig in kilometers per hour.
- **Agility**: Affects the pig's ability to navigate turns. Higher agility lessens the deceleration on corners.
- **Endurance**: Duration the pig can sustain its peak speed, measured in seconds.
- **Vigor**: Time taken for a pig to recover from exertion. A lower value indicates quicker recovery.
- **Spirit**: Likelihood of a pig entering a sprint phase mid-race.
- **Energy**: Interval at which the pig assesses the chance to sprint. Lower energy leads to more frequent sprints.

These attributes contribute to an overall **Performance Level** for each pig, which in turn informs the betting odds.

## Race Logic

Pigs can find themselves in one of three states during a race, each state indicating by a color change in the progress bar:

- **CHARGING**: The pig is sprinting at maximum speed (light blue).
- **NORMAL**: The pig trots at a standard pace (between light and dark green; darker greens indicate the pig racer is struggling with the track conditions more).
- **RECOVERING**: The pig slows below the usual speed to recuperate (red).

The `Energy` stat dictates the frequency of the pig's attempts to sprint, determined by the `Spirit` stat.

The racetrack includes straightaways and bends, where a pig's velocity is moderated by the track condition and its `Agility`.

Both weather and track conditions exert universal modifiers that influence the speed of all pigs.

As each pig crosses the finish line, its performance data is recorded, and the main interface is updated with a summary of the race results.

## Betting

Before the race commences, users can evaluate the pigs' statistics and odds to inform their betting decisions. Although the currency is virtual, the betting feature adds an engaging layer of strategy to the game.

The betting interface presents detailed information about the selected pig, including a breakdown of its performance metrics and real-time odds calculations.