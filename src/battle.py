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
        
        self.grid = np.zeros((self.height, self.width), dtype=int)
        
        self.step_count = 0
        self.combat_stats = {
            'kills': {1: 0, 2: 0},
            'losses': {1: 0, 2: 0},
            'territory': {1: 0.0, 2: 0.0}
        }
        
        self.initialize_grid()

    def initialize_grid(self):
        teams_config = self.config.get('teams', {})
        spawn_width = int(self.width * 0.3)
        
        for team_id, team_cfg in teams_config.items():
            pop_percent = team_cfg.get('initial_pop_percent', 0.2)
            
            if team_id == 1:
                x_start, x_end = 0, spawn_width
            else:
                x_start, x_end = self.width - spawn_width, self.width
            
            spawn_area = np.zeros((self.height, self.width), dtype=bool)
            spawn_area[:, x_start:x_end] = True
            
            random_grid = np.random.random((self.height, self.width))
            placement_mask = spawn_area & (random_grid < pop_percent)
            
            self.grid[placement_mask] = team_id
            
        self.terrain.conquest_map = self.grid.astype(int)

    def get_neighbor_counts(self, grid_mask):
        grid = grid_mask.astype(int)
        neighbors = np.zeros_like(grid, dtype=int)
        
        neighbors[1:, :] += grid[:-1, :]
        neighbors[:-1, :] += grid[1:, :]
        neighbors[:, 1:] += grid[:, :-1]
        neighbors[:, :-1] += grid[:, 1:]
        neighbors[1:, 1:] += grid[:-1, :-1]
        neighbors[1:, :-1] += grid[:-1, 1:]
        neighbors[:-1, 1:] += grid[1:, :-1]
        neighbors[:-1, :-1] += grid[1:, 1:]
        
        return neighbors

    def step(self) -> Dict:
        self.step_count += 1
        
        mask1 = (self.grid == 1)
        mask2 = (self.grid == 2)
        
        n1 = self.get_neighbor_counts(mask1)
        n2 = self.get_neighbor_counts(mask2)
        
        rules = self.config.get('automaton_rules', {})
        survival_threshold = set(rules.get('survival_threshold', [2, 3]))
        birth_threshold = set(rules.get('birth_threshold', [3]))
        enemy_tolerance = rules.get('enemy_tolerance', 3)
        
        next_grid = np.zeros_like(self.grid)
        
        survive_n1 = np.isin(n1, list(survival_threshold))
        survive_n2 = np.isin(n2, list(survival_threshold))
        
        safe_from_2 = (n2 <= enemy_tolerance)
        safe_from_1 = (n1 <= enemy_tolerance)
        
        t1_survives = mask1 & survive_n1 & safe_from_2
        t2_survives = mask2 & survive_n2 & safe_from_1
        
        next_grid[t1_survives] = 1
        next_grid[t2_survives] = 2
        
        died_t1_combat = mask1 & (n2 > enemy_tolerance)
        died_t2_combat = mask2 & (n1 > enemy_tolerance)
        
        self.combat_stats['losses'][1] += np.sum(died_t1_combat)
        self.combat_stats['losses'][2] += np.sum(died_t2_combat)
        self.combat_stats['kills'][2] += np.sum(died_t1_combat) 
        self.combat_stats['kills'][1] += np.sum(died_t2_combat) 
        
        empty_mask = (self.grid == 0)
        
        born_n1 = np.isin(n1, list(birth_threshold))
        born_n2 = np.isin(n2, list(birth_threshold))
        
        birth_t1_cand = empty_mask & born_n1
        birth_t2_cand = empty_mask & born_n2
        
        conflict = birth_t1_cand & birth_t2_cand
        
        t1_wins = conflict & (n1 > n2)
        t2_wins = conflict & (n2 > n1)
        
        final_birth_t1 = birth_t1_cand & (~conflict | t1_wins)
        final_birth_t2 = birth_t2_cand & (~conflict | t2_wins)
        
        next_grid[final_birth_t1] = 1
        next_grid[final_birth_t2] = 2
        
        self.grid = next_grid
        
        self.terrain.conquest_map = self.grid.astype(int)
        
        total_cells = self.width * self.height
        if total_cells > 0:
            self.combat_stats['territory'][1] = (np.sum(next_grid == 1) / total_cells) * 100
            self.combat_stats['territory'][2] = (np.sum(next_grid == 2) / total_cells) * 100

        return self.get_battle_stats()

    def get_battle_stats(self) -> Dict:
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