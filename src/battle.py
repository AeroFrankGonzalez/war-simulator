# battle.py - No necesita cambios en su lógica principal por ahora.
# El código sigue siendo el que proporcionaste:

from typing import List, Dict, Tuple
import numpy as np
from unit import Unit
from terrain import Terrain # Asegúrate de que esta importación sea correcta

class Battle:
    def __init__(self, terrain: Terrain, contact_radius: float = 1.0):
        self.terrain = terrain
        self.units: Dict[int, List[Unit]] = {}  # team_id -> list of units
        self.contact_radius = contact_radius
        self.step_count = 0
        self.combat_stats = {
            'kills': {},
            'losses': {},
            'territory': {}
        }

    def add_unit(self, unit: Unit) -> None:
        """Add a unit to the battle"""
        if unit.team_id not in self.units:
            self.units[unit.team_id] = []
        self.units[unit.team_id].append(unit)

    def step(self) -> Dict:
        """Execute one step of the battle simulation"""
        self.step_count += 1

        # Process unit movements and combat
        for team_id, team_units in self.units.items():
            for unit in team_units:
                # Obtain terrain modifier before moving
                x, y = int(unit.position[0]), int(unit.position[1])
                terrain_mod = self.terrain.get_movement_modifier(x, y)
                # Pass terrain_bounds to move method (already present in your code)
                terrain_bounds = (self.terrain.width, self.terrain.height)
                unit.move(unit.target, terrain_mod, terrain_bounds)


        # Process combat (unchanged)
        casualties = []
        for team1_id, team1_units in self.units.items():
            # Create a temporary list to iterate over to avoid issues with removing elements
            team1_units_copy = list(team1_units)
            for unit1 in team1_units_copy:
                 # Check if unit1 is still alive after previous combat
                 if unit1.health > 0:
                    for team2_id, team2_units in self.units.items():
                        if team1_id != team2_id:  # Don't process friendly fire
                            # Create a temporary list for team2 units as well
                            team2_units_copy = list(team2_units)
                            for unit2 in team2_units_copy:
                                if unit2.health > 0 and unit1.is_in_contact_range(unit2, self.contact_radius):
                                    if unit2.take_damage():
                                        casualties.append((team2_id, unit2))
                                        unit1.kills += 1 # Credit kill to unit1

        # Remove casualties and update stats
        for team_id, dead_unit in casualties:
             # Check if the unit is still in the list before trying to remove it
             if dead_unit in self.units.get(team_id, []):
                self.units[team_id].remove(dead_unit)
                if team_id not in self.combat_stats['losses']:
                    self.combat_stats['losses'][team_id] = 0
                self.combat_stats['losses'][team_id] += 1
            # You might want to clean up units with health <= 0 at the end of combat processing

        # A more robust way to handle casualties might be to collect them first,
        # and then remove them after all combat for the step is processed.
        # Let's refine the casualty removal:
        alive_units: Dict[int, List[Unit]] = {}
        for team_id, team_units in self.units.items():
            alive_units[team_id] = [unit for unit in team_units if unit.health > 0]
        self.units = alive_units # Update the units dictionary

        # Update territory control (uses the updated Terrain.update_conquest)
        unit_positions = {
            team_id: [(u.position[0], u.position[1]) for u in units if u.health > 0] # Only use positions of living units
            for team_id, units in self.units.items()
        }
        self.terrain.update_conquest(unit_positions)

        # Update territory stats
        for team_id in self.units.keys():
            self.combat_stats['territory'][team_id] = self.terrain.get_conquest_percentage(team_id)

        # Check if a team has been eliminated to potentially end the battle early
        remaining_teams = [team_id for team_id, units in self.units.items() if units]
        if len(remaining_teams) <= 1:
             # Battle ends, return final stats
             return self.get_battle_stats()

        return self.get_battle_stats() # Return current stats if battle continues


    def get_battle_stats(self) -> Dict:
        """Return current battle statistics"""
        stats = {
            'step': self.step_count,
            'units_remaining': {team_id: len(units) for team_id, units in self.units.items()},
            'territory_control': self.combat_stats['territory'],
            'casualties': self.combat_stats['losses'],
            'total_kills': {
                team_id: sum(unit.kills for unit in units)
                for team_id, units in self.units.items()
            }
        }
        return stats