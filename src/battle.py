from typing import List, Dict, Tuple
import numpy as np
import random
from unit import Unit
from terrain import Terrain

class Battle:
    def __init__(self, terrain: Terrain, config: dict):
        self.terrain = terrain
        self.config = config
        self.width = terrain.width
        self.height = terrain.height
        
        # Grid to store Unit objects (or None for empty cells).
        # Using object array to store Unit references. 
        # Alternatively, could use efficient int arrays for team_id if Unit has no other state.
        # For now, keeping Unit objects to allow for potential future state (veterancy, etc).
        self.grid = np.empty((self.height, self.width), dtype=object)
        
        self.step_count = 0
        self.combat_stats = {
            'kills': {1: 0, 2: 0},
            'losses': {1: 0, 2: 0},
            'territory': {1: 0.0, 2: 0.0}
        }
        
        self.initialize_grid()

    def initialize_grid(self):
        """Populate the grid with initial units based on configuration."""
        teams_config = self.config.get('teams', {})
        
        # Determine spawn areas (e.g., Left vs Right split)
        # Team 1: Left 30%
        # Team 2: Right 30%
        spawn_width = int(self.width * 0.3)
        
        for team_id, team_cfg in teams_config.items():
            pop_percent = team_cfg.get('initial_pop_percent', 0.2)
            
            # Define x range for this team
            if team_id == 1:
                x_start, x_end = 0, spawn_width
            else:
                x_start, x_end = self.width - spawn_width, self.width
                
            for y in range(self.height):
                for x in range(x_start, x_end):
                    if random.random() < pop_percent:
                        self.grid[y, x] = Unit(team_id=team_id)

    def count_neighbors(self, x, y):
        """
        Count neighbors for a cell (x, y).
        Returns specific counts for each team to handle combat logic.
        """
        counts = {1: 0, 2: 0}
        
        # Moore neighborhood (8 neighbors)
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                    
                nx, ny = x + dx, y + dy
                
                # Boundary check
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    unit = self.grid[ny, nx]
                    if unit:
                        counts[unit.team_id] += 1
                        
        return counts

    def step(self) -> Dict:
        """Execute one step of the Cellular Automaton simulation"""
        self.step_count += 1
        
        # Create a new grid for the next state
        next_grid = np.empty((self.height, self.width), dtype=object)
        
        # Track changing stats for this step
        step_kills = {1: 0, 2: 0}
        step_losses = {1: 0, 2: 0}
        
        rules = self.config.get('automaton_rules', {})
        survival_threshold = rules.get('survival_threshold', [2, 3]) # Neighbors to survive
        birth_threshold = rules.get('birth_threshold', [3])        # Neighbors to be born
        enemy_tolerance = rules.get('enemy_tolerance', 3)          # Max enemies before death
        
        # Iterate over every cell
        for y in range(self.height):
            for x in range(self.width):
                current_unit = self.grid[y, x]
                neighbors = self.count_neighbors(x, y)
                
                # Logic for an OCCUPIED cell
                if current_unit:
                    team_id = current_unit.team_id
                    allies = neighbors[team_id]
                    # Calculate enemies (sum of all other teams)
                    enemies = sum(count for tid, count in neighbors.items() if tid != team_id)
                    
                    # Rule 1: Combat / Overcrowding by enemies
                    if enemies > enemy_tolerance:
                        next_grid[y, x] = None # Dies due to enemy overwhelming
                        step_losses[team_id] += 1
                        # Award kills roughly to the dominant enemy? 
                        # Simplified: Award to 'the enemy' (assuming 2 teams)
                        enemy_id = 1 if team_id == 2 else 2
                        step_kills[enemy_id] += 1
                        continue

                    # Rule 2: Game of Life Survival (Based on ALLIES)
                    # Standard GoL: Dies if < 2 allies (isolation) or > 3 allies (overcrowding)
                    if allies in survival_threshold:
                        next_grid[y, x] = current_unit # Survives
                    else:
                        next_grid[y, x] = None # Dies (Isolation or Overcrowding)
                        # Natural causes, not combat kill
                
                # Logic for an EMPTY cell
                else:
                    # Rule 3: Reproduction / Birth
                    # Check if any team meets birth threshold
                    candidates = []
                    for team_id, count in neighbors.items():
                        if count in birth_threshold:
                            candidates.append(team_id)
                            
                    if len(candidates) == 1:
                        # Clear winner for birth
                        next_grid[y, x] = Unit(team_id=candidates[0])
                    elif len(candidates) > 1:
                        # Contested birth! 
                        # Option A: No birth (deadlock)
                        # Option B: Random (chaos)
                        # Option C: Team with MORE neighbors wins
                        
                        # Let's go with Option C:
                        max_neighbors = -1
                        winner_id = None
                        for team_id in candidates:
                            if neighbors[team_id] > max_neighbors:
                                max_neighbors = neighbors[team_id]
                                winner_id = team_id
                            elif neighbors[team_id] == max_neighbors:
                                winner_id = None # Tie prevents birth
                        
                        if winner_id:
                            next_grid[y, x] = Unit(team_id=winner_id)

        # Update grid state
        self.grid = next_grid
        
        # Update persistent stats
        for team_id in [1, 2]:
            self.combat_stats['kills'][team_id] += step_kills[team_id]
            self.combat_stats['losses'][team_id] += step_losses[team_id]
            
        # Update territory control based on unit presence
        # (Simply count occupied cells for now, simpler than Influence Map for CA)
        total_cells = self.width * self.height
        for team_id in [1, 2]:
             # Count cells occupied by this team
             count = 0
             for y in range(self.height):
                 for x in range(self.width):
                     u = self.grid[y, x]
                     if u and u.team_id == team_id:
                         count += 1
             self.combat_stats['territory'][team_id] = (count / total_cells) * 100

        return self.get_battle_stats()

    def get_battle_stats(self) -> Dict:
        """Return current battle statistics"""
        
        # Count current units efficiently
        unit_counts = {1: 0, 2: 0}
        for y in range(self.height):
            for x in range(self.width):
                u = self.grid[y, x]
                if u:
                    unit_counts[u.team_id] = unit_counts.get(u.team_id, 0) + 1

        stats = {
            'step': self.step_count,
            'units_remaining': unit_counts,
            'territory_control': self.combat_stats['territory'],
            'casualties': self.combat_stats['losses'],
            'total_kills': self.combat_stats['kills']
        }
        return stats