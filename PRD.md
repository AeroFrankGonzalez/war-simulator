# Product Requirements Document (PRD)

**Project Title:** War Simulation Sandbox

**Version:** 1.0

**Date:** April 22, 2025

**Author:** Frank Gonzalez

---

## 1. Introduction

This document outlines the requirements for a Python-based war simulation sandbox. The goal is to create a flexible, visually intuitive, and performance-conscious simulation where two opposing teams (or "bands") engage in conflict on a configurable terrain. The simulation should allow users to adjust team parameters, terrain characteristics, and observe the progress and outcome of the conflict in real-time, with the ability to export results for analysis.

## 2. Goals

* Develop a functional war simulation engine in Python.
* Provide a user interface (UI) to visualize the simulation state and control its execution.
* Allow extensive configuration of teams and terrain.
* Ensure smooth visualization and efficient memory usage for simulations involving a moderate number of units.
* Implement clear victory conditions based on team annihilation or terrain conquest.
* Enable the export of simulation parameters and final results.

## 3. User Stories (Optional but Recommended)

* As a user, I want to be able to set up two teams with different starting sizes and behaviors so I can see how different initial conditions affect the outcome.
* As a user, I want to define a custom terrain with obstacles like mountains and forests so I can see how the environment influences unit movement and strategy.
* As a user, I want to see a real-time scoreboard showing casualties, reinforcements, and current unit counts so I can follow the progress of the battle.
* As a user, I want to pause, resume, and reset the simulation so I can study specific moments or rerun scenarios easily.
* As a user, I want to export the final results, including parameters and outcomes, to a CSV file so I can analyze multiple simulation runs externally.
* As a user, I want to clearly see which areas of the map each team has conquered so I can track the progress towards a territorial victory.
* As a user, I want to configure basic strategic behaviors for each team (e.g., aggressive push, defensive posture) to influence their actions.

## 4. Functional Requirements

### 4.1. Simulation Core

* **REQ-SIM-1:** The simulation shall run based on discrete time steps or frames.
* **REQ-SIM-2:** The simulation loop shall update the state of all units and the terrain at each step.
* **REQ-SIM-3:** The simulation shall continue until a victory condition is met or the user manually ends it.

### 4.2. Team Management

* **REQ-TEAM-1:** The simulation shall support exactly two opposing teams/bands.
* **REQ-TEAM-2:** Users shall be able to configure initial parameters for each team:
    * **REQ-TEAM-2.1:** Initial number of units.
    * **REQ-TEAM-2.2:** Natural death rate (units per time step or percentage per time step).
    * **REQ-TEAM-2.3:** Base movement speed multiplier.
    * **REQ-TEAM-2.4:** Starting side of the map (e.g., Left vs. Right, Top vs. Bottom).
    * **REQ-TEAM-2.5:** Specific starting point (a single coordinate) for all initial units of that team.
    * **REQ-TEAM-2.6:** Configurable strategy/behavior pattern (see REQ-UNIT-4).
* **REQ-TEAM-3:** Teams shall be assigned distinct visual identifiers (e.g., colors, unit shapes - see REQ-UI-5).

### 4.3. Unit Management

* **REQ-UNIT-1:** Units shall be represented as simple visual elements (e.g., dots).
* **REQ-UNIT-2:** Units shall have attributes:
    * Team affiliation.
    * Current position (x, y).
    * Movement vector/target.
    * Current "health" or contact resistance (initially 5 points - see REQ-COMBAT-1).
    * Individual stats (optional: distance moved, enemies killed).
* **REQ-UNIT-3:** Unit movement shall be influenced by terrain properties (see REQ-TERRAIN-3). Units shall move slower in areas of high height or density and faster in areas of low height or density (within limits defined by the team's base speed).
* **REQ-UNIT-4:** Each team's units shall follow a configurable strategic behavior pattern:
    * **REQ-UNIT-4.1:** Examples of patterns to implement (at least a few initial options):
        * Aggressive advance towards the enemy starting side/point.
        * Seek and destroy (move towards the nearest enemy unit).
        * Defensive (stay near the team's starting area).
        * Flanking (attempt to move around obstacles to attack from the side).
        * Swarming (move as a tight group).
        * Dispersed (move to spread out across the terrain).
    * **REQ-UNIT-4.2:** The specific implementation of these strategies needs further design but should be driven by the team's configuration.
* **REQ-UNIT-5:** Units shall have a chance of "natural death" based on the team's configured rate. This is separate from combat death.

### 4.4. Terrain Management

* **REQ-TERRAIN-1:** The simulation shall take place on a 2D, square grid-based terrain.
* **REQ-TERRAIN-2:** The terrain shall have adjustable properties at different grid locations:
    * **REQ-TERRAIN-2.1:** Height (affecting movement speed).
    * **REQ-TERRAIN-2.2:** Density (affecting movement speed).
    * **REQ-TERRAIN-2.3:** Visual features/colors (representing height, density, or specific types like water, forest, desert).
* **REQ-TERRAIN-3:** Unit movement speed shall be modified based on the terrain properties of the unit's current location.
* **REQ-TERRAIN-4:** The system shall include at least 10 distinct pre-defined terrain maps/configurations.
* **REQ-TERRAIN-5:** The terrain shall visually represent the areas conquered by each team (see REQ-CONQUEST-2).

### 4.5. Combat and Scoring

* **REQ-COMBAT-1:** Combat shall occur when units from opposing teams are in close proximity ("contact").
* **REQ-COMBAT-2:** Each unit shall have a contact resistance/life counter, starting at 5.
* **REQ-COMBAT-3:** When an enemy unit makes "contact" (within a defined small radius) with a unit, the contacted unit's resistance shall decrease by 1.
* **REQ-COMBAT-4:** If a unit's resistance reaches 0, it is removed from the simulation (dies).
* **REQ-COMBAT-5:** When a unit dies due to enemy contact, the team responsible for the killing blow (or the contact that brought resistance to 0) gains 1 point. (Note: This scoring is for tracking, not a victory condition).

### 4.6. Terrain Conquest

* **REQ-CONQUEST-1:** A terrain grid cell is considered "conquered" by a team if a unit from that team has been the last unit to occupy that cell for a defined duration or number of steps.
* **REQ-CONQUEST-2:** Conquered terrain shall be visually indicated on the map (e.g., a transparent overlay color corresponding to the conquering team).
* **REQ-CONQUEST-3:** The UI shall display the percentage of the terrain conquered by each team.

### 4.7. User Interface (UI)

* **REQ-UI-1:** The UI shall display the terrain map with its features.
* **REQ-UI-2:** The UI shall display the units of both teams on the map according to their current positions.
* **REQ-UI-3:** The UI shall display the terrain conquest status (see REQ-CONQUEST-2).
* **REQ-UI-4:** The UI shall include a status panel with real-time information:
    * **REQ-UI-4.1:** Current simulation time/steps.
    * **REQ-UI-4.2:** Number of units currently alive for each team.
    * **REQ-UI-4.3:** Total units lost to natural death for each team.
    * **REQ-UI-4.4:** Total units lost due to enemy action for each team.
    * **REQ-UI-4.5:** Total units spawned (if applicable, although the prompt doesn't explicitly mention spawning after the start - clarify this in design).
    * **REQ-UI-4.6:** Current score (based on enemy kills) for each team.
    * **REQ-UI-4.7:** Percentage of terrain conquered by each team.
    * **REQ-UI-4.8:** Current "percentage of victory" (a metric combining live units, score, and terrain conquest - requires design definition of the formula).
* **REQ-UI-5:** Unit colors shall contrast well with the terrain colors. Suggested initial colors: WHITE for one team, BLACK for the other, assuming the terrain uses other colors.
* **REQ-UI-6:** The UI shall include control buttons:
    * **REQ-UI-6.1:** Start Simulation.
    * **REQ-UI-6.2:** Pause Simulation.
    * **REQ-UI-6.3:** Resume Simulation.
    * **REQ-UI-6.4:** Reset Simulation (return to initial state).
    * **REQ-UI-6.5:** End Simulation (immediately stop and show final results).
    * **REQ-UI-6.6:** Export Results.
* **REQ-UI-7:** There shall be a configuration screen or panel to set initial team parameters and choose the terrain.

### 4.8. Simulation Control and Game End

* **REQ-CONTROL-1:** The simulation starts when the user clicks "Start".
* **REQ-CONTROL-2:** The simulation pauses when the user clicks "Pause".
* **REQ-CONTROL-3:** The simulation resumes from the paused state when the user clicks "Resume".
* **REQ-CONTROL-4:** The simulation resets to its initial state (based on current configuration) when the user clicks "Reset".
* **REQ-CONTROL-5:** The simulation stops immediately when the user clicks "End Simulation".
* **REQ-CONTROL-6:** The simulation automatically ends when a victory condition is met:
    * **REQ-CONTROL-6.1:** One team has zero units remaining.
    * **REQ-CONTROL-6.2:** One team has conquered a user-defined percentage of the terrain (e.g., 70%, adjustable in configuration).
* **REQ-CONTROL-7:** Upon simulation end (either manual or automatic), the final results (as per REQ-DATA-2) shall be displayed or made available for export.
* **REQ-CONTROL-8:** After simulation end, the user shall be able to restart with the same parameters or modify parameters for a new simulation.

### 4.9. Data Export

* **REQ-DATA-1:** The user shall be able to export the final simulation results by clicking the "Export Results" button.
* **REQ-DATA-2:** The exported data shall include:
    * **REQ-DATA-2.1:** Initial parameters for both teams (units, death rate, speed, starting side/point, chosen strategy).
    * **REQ-DATA-2.2:** Chosen terrain configuration.
    * **REQ-DATA-2.3:** Final simulation time/steps.
    * **REQ-DATA-2.4:** Final number of units for each team.
    * **REQ-DATA-2.5:** Total natural deaths for each team.
    * **REQ-DATA-2.6:** Total combat deaths for each team.
    * **REQ-DATA-2.7:** Final score (enemy kills) for each team.
    * **REQ-DATA-2.8:** Final terrain conquest percentage for each team.
    * **REQ-DATA-2.9:** Winning team (if any), or draw/manual end status.
* **REQ-DATA-3:** The export format shall be either CSV or JSON, selectable by the user or a pre-defined standard. CSV is preferred for ease of spreadsheet analysis.
* **REQ-DATA-4:** The user shall be able to specify the folder where the export file is saved.

## 5. Non-Functional Requirements

* **NFR-PERF-1:** **Performance:** The simulation and visualization should be as fluid as possible, minimizing lag during execution, especially with a moderate number of units (e.g., up to a few hundred per side).
* **NFR-PERF-2:** **Memory Usage:** The simulation should be designed to avoid excessive memory consumption, allowing it to run for extended periods without issues. Data structures and algorithms should be chosen with memory efficiency in mind.
* **NFR-USAB-1:** **Usability:** The UI should be intuitive and easy to understand, allowing users to quickly configure simulations and interpret the displayed information.
* **NFR-USAB-2:** **Visual Clarity:** The visualization of the terrain, units, and conquest areas should be clear and easy to distinguish, even during fast-paced simulation.
* **NFR-ROB-1:** **Robustness:** The simulation should handle edge cases gracefully (e.g., zero initial units, teams starting in invalid locations - although starting point is specified, validation might be needed).

## 6. Scope

**In Scope:**

* Core simulation logic (unit movement, combat, death).
* Configurable team parameters.
* Configurable grid-based terrain with height and density properties.
* At least 10 distinct terrain presets.
* Basic unit strategic behaviors as defined in REQ-UNIT-4.
* Real-time UI display of simulation state, units, terrain, and statistics.
* Simulation controls (Start, Pause, Resume, Reset, End).
* Victory conditions (annihilation, terrain conquest percentage).
* Data export in CSV or JSON format.
* Visual representation of terrain conquest.

**Out of Scope (for this initial version):**

* Advanced AI or complex tactical planning beyond the configurable strategies.
* Unit types with different abilities or stats (all units are currently assumed identical within a team, except for position/state).
* Reinforcements appearing dynamically during the simulation (unless explicitly added as a team parameter later).
* Multiplayer capabilities.
* Complex graphical effects or animations beyond simple position updates and color changes.
* Sound effects.
* Saving/loading of simulation *states* (only parameters and final results are exported).

## 7. Metrics for Success

* All defined functional requirements are implemented.
* The simulation runs smoothly and without significant lag with up to [Define a specific number, e.g., 500] units per side on a standard development machine.
* Memory usage remains stable and within reasonable limits during extended simulation runs.
* Users can successfully configure teams and terrain, run simulations, and export meaningful results.
* The UI clearly visualizes the simulation state and provides all required statistics.
* Victory conditions are correctly detected and end the simulation.

## 8. Future Considerations

* Adding different unit types with varied attributes (speed, combat strength, range).
* Implementing more complex and hierarchical strategic behaviors for teams.
* Adding a visual terrain editor.
* Including options for dynamic events during the simulation (e.g., weather, random events).
* Expanding data export to include simulation state snapshots at intervals.

---
