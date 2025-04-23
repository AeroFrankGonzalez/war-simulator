from typing import List, Dict, Tuple
import numpy as np
from unit import Unit
from terrain import Terrain

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
                if unit.target is not None:
                    # Get terrain modifier for current position
                    x, y = int(unit.position[0]), int(unit.position[1])
                    terrain_mod = self.terrain.get_movement_modifier(x, y)
                    unit.move(unit.target, terrain_mod)

        # Process combat
        casualties = []
        for team1_id, team1_units in self.units.items():
            for team2_id, team2_units in self.units.items():
                if team1_id != team2_id:  # Don't process friendly fire
                    for unit1 in team1_units:
                        for unit2 in team2_units:
                            if unit1.is_in_contact_range(unit2, self.contact_radius):
                                if unit2.take_damage():
                                    casualties.append((team2_id, unit2))
                                    unit1.kills += 1

        # Remove casualties and update stats
        for team_id, dead_unit in casualties:
            self.units[team_id].remove(dead_unit)
            if team_id not in self.combat_stats['losses']:
                self.combat_stats['losses'][team_id] = 0
            self.combat_stats['losses'][team_id] += 1

        # Update territory control
        unit_positions = {
            team_id: [(u.position[0], u.position[1]) for u in units]
            for team_id, units in self.units.items()
        }
        self.terrain.update_conquest(unit_positions)

        # Update territory stats
        for team_id in self.units.keys():
            self.combat_stats['territory'][team_id] = self.terrain.get_conquest_percentage(team_id)

        return self.get_battle_stats()

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