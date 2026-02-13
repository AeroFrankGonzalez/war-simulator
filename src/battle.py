from typing import List, Dict, Tuple
import numpy as np
import random
from terrain import Terrain

class Battle:
    def __init__(self, terrain: Terrain, config: dict):
        self.terrain = terrain
        self.config = config
        self.width = terrain.width
        self.height = terrain.height
        
        # Grid to store team IDs (int). 0 = Empty, 1 = Team 1, 2 = Team 2.
        # Vectorized operations require simple types like int or float, not objects.
        self.grid = np.zeros((self.height, self.width), dtype=int)
        
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
        spawn_width = int(self.width * 0.3)
        
        for team_id, team_cfg in teams_config.items():
            pop_percent = team_cfg.get('initial_pop_percent', 0.2)
            
            if team_id == 1:
                x_start, x_end = 0, spawn_width
            else:
                x_start, x_end = self.width - spawn_width, self.width
            
            # Create a mask for the spawn area
            spawn_area = np.zeros((self.height, self.width), dtype=bool)
            spawn_area[:, x_start:x_end] = True
            
            # Generate random placement within spawn area
            random_grid = np.random.random((self.height, self.width))
            # Place units where active in spawn area and random check passes
            placement_mask = spawn_area & (random_grid < pop_percent)
            
            # Assign team ID to the grid
            self.grid[placement_mask] = team_id

    def get_neighbor_counts(self, grid_mask):
        """
        Calculate neighbor counts for a boolean grid mask using array slicing.
        Handles hard borders (zero padding) by slicing.
        """
        # Convert boolean mask to int for summation
        grid = grid_mask.astype(int)
        neighbors = np.zeros_like(grid, dtype=int)
        
        # Add shifted versions (8 directions)
        # Up
        neighbors[1:, :] += grid[:-1, :]
        # Down
        neighbors[:-1, :] += grid[1:, :]
        # Left
        neighbors[:, 1:] += grid[:, :-1]
        # Right
        neighbors[:, :-1] += grid[:, 1:]
        # Up-Left
        neighbors[1:, 1:] += grid[:-1, :-1]
        # Up-Right
        neighbors[1:, :-1] += grid[:-1, 1:]
        # Down-Left
        neighbors[:-1, 1:] += grid[1:, :-1]
        # Down-Right
        neighbors[:-1, :-1] += grid[1:, 1:]
        
        return neighbors

    def step(self) -> Dict:
        """Execute one step of the Cellular Automaton simulation using Vectorized Logic."""
        self.step_count += 1
        
        # 1. Calculate masks for each team
        mask1 = (self.grid == 1)
        mask2 = (self.grid == 2)
        
        # 2. Count neighbors for each team
        n1 = self.get_neighbor_counts(mask1)
        n2 = self.get_neighbor_counts(mask2)
        
        # 3. Apply Rules
        rules = self.config.get('automaton_rules', {})
        survival_threshold = set(rules.get('survival_threshold', [2, 3]))
        birth_threshold = set(rules.get('birth_threshold', [3]))
        enemy_tolerance = rules.get('enemy_tolerance', 3)
        
        # Prepare next grid (start empty)
        next_grid = np.zeros_like(self.grid)
        
        # --- Survival & Death (for occupied cells) ---
        # Team 1 Survival:
        # Has Team 1? AND Neighbors1 in survival? AND Neighbors2 <= tolerance?
        
        # Create survival masks based on neighbor counts.
        # np.isin is useful for checking if count is in the allowed set [2, 3] etc.
        survive_n1 = np.isin(n1, list(survival_threshold))
        survive_n2 = np.isin(n2, list(survival_threshold))
        
        # Check enemy tolerance
        safe_from_2 = (n2 <= enemy_tolerance)
        safe_from_1 = (n1 <= enemy_tolerance)
        
        # Determine who survives
        # Team 1 survives if: bit is 1, allies are good, enemies are low
        t1_survives = mask1 & survive_n1 & safe_from_2
        # Team 2 survives if: bit is 2, allies are good, enemies are low
        t2_survives = mask2 & survive_n2 & safe_from_1
        
        # Add survivors to next grid
        next_grid[t1_survives] = 1
        next_grid[t2_survives] = 2
        
        # Track losses (Occupied BEFORE but NOT in next_grid)
        # Note: This simple logic counts ALL disappearances as losses (died to rules or enemies)
        # To distinguish combat kills specifically would require more complex mask logic, 
        # but for stats, 'losses' usually implies death by any cause in CA.
        # If we want specific 'killed by enemy' vs 'died of loneliness', we can refine.
        # Let's count "killed by enemy" specifically for the stats.
        died_t1_combat = mask1 & (n2 > enemy_tolerance)
        died_t2_combat = mask2 & (n1 > enemy_tolerance)
        
        self.combat_stats['losses'][1] += np.sum(died_t1_combat)
        self.combat_stats['losses'][2] += np.sum(died_t2_combat)
        # Award kills
        self.combat_stats['kills'][2] += np.sum(died_t1_combat) # Team 2 killed T1
        self.combat_stats['kills'][1] += np.sum(died_t2_combat) # Team 1 killed T2
        
        
        # --- Birth (for empty cells) ---
        empty_mask = (self.grid == 0)
        
        # Birth candidates
        born_n1 = np.isin(n1, list(birth_threshold))
        born_n2 = np.isin(n2, list(birth_threshold))
        
        # Potential births
        birth_t1_cand = empty_mask & born_n1
        birth_t2_cand = empty_mask & born_n2
        
        # Resolve conflicts (both want to be born in same empty cell)
        conflict = birth_t1_cand & birth_t2_cand
        
        # Winner based on who has MORE neighbors? Or strictly random? 
        # Plan says: Majority wins.
        # Where conflict, check neighbor counts:
        t1_wins = conflict & (n1 > n2)
        t2_wins = conflict & (n2 > n1)
        # Ties in conflict -> No birth (deadlock)
        
        # Final birth masks
        # Born T1 if: Candidate AND (Not Conflict OR (Conflict and Win))
        final_birth_t1 = birth_t1_cand & (~conflict | t1_wins)
        final_birth_t2 = birth_t2_cand & (~conflict | t2_wins)
        
        # Apply births
        next_grid[final_birth_t1] = 1
        next_grid[final_birth_t2] = 2
        
        # --- Update State ---
        self.grid = next_grid
        
        # Update territory stats
        total_cells = self.width * self.height
        if total_cells > 0:
            self.combat_stats['territory'][1] = (np.sum(next_grid == 1) / total_cells) * 100
            self.combat_stats['territory'][2] = (np.sum(next_grid == 2) / total_cells) * 100

        return self.get_battle_stats()

    def get_battle_stats(self) -> Dict:
        """Return current battle statistics"""
        stats = {
            'step': self.step_count,
            'units_remaining': {
                1: int(np.sum(self.grid == 1)),
                2: int(np.sum(self.grid == 2))
            },
            'territory_control': self.combat_stats['territory'],
            'casualties': self.combat_stats['losses'],
            'total_kills': self.combat_stats['kills']
        }
        return stats