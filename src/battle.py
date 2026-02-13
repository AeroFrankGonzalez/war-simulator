from typing import Dict
import numpy as np
from terrain import Terrain

class Battle:
    def __init__(self, terrain: Terrain, config: dict):
        self.terrain = terrain
        self.config = config
        self.width = terrain.width
        self.height = terrain.height
        
        # 0 = Empty, 1 = Cyan, 2 = Neon
        self.grid = np.zeros((self.height, self.width), dtype=np.int8)
        self.ages = np.zeros((self.height, self.width), dtype=np.int16)
        
        # Influence Map (-100.0 to +100.0)
        self.influence = np.zeros((self.height, self.width), dtype=np.float32)
        
        # Scorch Grid
        self.cemetery = np.zeros((self.height, self.width), dtype=np.int8)
        
        self.step_count = 0
        self.combat_stats = {
            'kills': {1: 0, 2: 0},
            'losses': {1: 0, 2: 0},
            'territory': {1: 0.0, 2: 0.0},
            'conquest_score': {1: 0, 2: 0}
        }
        
        self.initialize_grid()

    def initialize_grid(self):
        self.grid.fill(0)
        self.ages.fill(0)
        self.influence.fill(0)
        self.cemetery.fill(0)
        
        teams_config = self.config.get('teams', {})
        spawn_width = int(self.width * 0.3)
        
        for team_id, team_cfg in teams_config.items():
            val = team_cfg.get('initial_pop_percent', 0.2)
            pop_percent = float(val) if val is not None else 0.2
            team_id = int(team_id)
            
            # Perfect Symmetry Spawn
            if team_id == 1:
                x_start, x_end = 0, spawn_width
            else:
                x_start, x_end = self.width - spawn_width, self.width
            
            spawn_area = np.zeros((self.height, self.width), dtype=bool)
            spawn_area[:, x_start:x_end] = True
            
            random_grid = np.random.random((self.height, self.width))
            placement_mask = spawn_area & (random_grid < pop_percent)
            
            self.grid[placement_mask] = team_id

    def get_neighbor_counts(self, grid_mask):
        grid = grid_mask.astype(np.int8)
        neighbors = np.zeros_like(grid, dtype=np.int8)
        
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
        
        # 1. Update Scorch/Cemetery
        self.cemetery = np.maximum(0, self.cemetery - 1)
        
        # 2. Update Influence
        self.influence *= 0.95 
        mask1 = (self.grid == 1)
        mask2 = (self.grid == 2)
        self.influence[mask1] += 5.0
        self.influence[mask2] -= 5.0
        self.influence = np.clip(self.influence, -100.0, 100.0)
        
        # 3. CA Logic
        n1 = self.get_neighbor_counts(mask1)
        n2 = self.get_neighbor_counts(mask2)
        
        rules = self.config.get('automaton_rules', {})
        survival_threshold = list(rules.get('survival_threshold', [2, 3]))
        birth_threshold = list(rules.get('birth_threshold', [3]))
        enemy_tolerance = rules.get('enemy_tolerance', 3)
        aging_rules = rules.get('aging', {})
        max_age = aging_rules.get('max_age', 60)
        death_chance = aging_rules.get('old_age_death_chance', 0.10)
        
        next_grid = np.zeros_like(self.grid)
        next_ages = np.zeros_like(self.ages)
        
        # Survival
        survive_n1 = np.isin(n1, survival_threshold)
        survive_n2 = np.isin(n2, survival_threshold)
        safe_from_2 = (n2 <= enemy_tolerance)
        safe_from_1 = (n1 <= enemy_tolerance)
        t1_survives = mask1 & survive_n1 & safe_from_2
        t2_survives = mask2 & survive_n2 & safe_from_1
        
        # Aging / Scorch
        if aging_rules.get('enabled', True):
            is_old_t1 = t1_survives & (self.ages > max_age)
            is_old_t2 = t2_survives & (self.ages > max_age)
            
            random_roll = np.random.random(self.ages.shape)
            dies_of_age_t1 = is_old_t1 & (random_roll < death_chance)
            dies_of_age_t2 = is_old_t2 & (random_roll < death_chance)
            
            self.cemetery[dies_of_age_t1] = 10
            self.cemetery[dies_of_age_t2] = 10
            
            t1_survives &= (~dies_of_age_t1)
            t2_survives &= (~dies_of_age_t2)
            
            next_ages[t1_survives] = self.ages[t1_survives] + 1
            next_ages[t2_survives] = self.ages[t2_survives] + 1
        else:
            next_ages[t1_survives] = self.ages[t1_survives] + 1
            next_ages[t2_survives] = self.ages[t2_survives] + 1

        next_grid[t1_survives] = 1
        next_grid[t2_survives] = 2
        
        # Birth (Balanced)
        empty_mask = (self.grid == 0)
        fertile_ground = (self.cemetery == 0)
        
        born_n1 = np.isin(n1, birth_threshold)
        born_n2 = np.isin(n2, birth_threshold)
        
        birth_t1_cand = empty_mask & born_n1 & fertile_ground
        birth_t2_cand = empty_mask & born_n2 & fertile_ground
        
        conflict = birth_t1_cand & birth_t2_cand
        
        # STOCHASTIC TIE-BREAKER FOR FAIRNESS
        # If both want to be born, and neighbor counts are equal (or unequal), 
        # we strictly check majority. If majority tied, COIN FLIP.
        
        # Tie condition: strictly equal influence or just simultaneous eligibility?
        # Standard Game of Life assumes count matches threshold.
        # But who wins the spot? 
        # Logic: If n1 > n2, T1 likely has more support. 
        # If n1 == n2, pure 50/50.
        
        tie = conflict & (n1 == n2)
        tie_winner_t1 = np.zeros_like(tie, dtype=bool)
        
        if np.any(tie):
            random_toss = np.random.random(tie.shape)
            tie_winner_t1 = tie & (random_toss < 0.5)
        
        t1_wins_conflict = conflict & ((n1 > n2) | tie_winner_t1)
        t2_wins_conflict = conflict & ((n2 > n1) | (tie & ~tie_winner_t1))
        
        final_birth_t1 = birth_t1_cand & (~conflict | t1_wins_conflict)
        final_birth_t2 = birth_t2_cand & (~conflict | t2_wins_conflict)
        
        next_grid[final_birth_t1] = 1
        next_grid[final_birth_t2] = 2
        
        self.grid = next_grid
        self.ages = next_ages
        
        # Stats
        total_cells = self.width * self.height
        if total_cells > 0:
            self.combat_stats['territory'][1] = (np.sum(next_grid == 1) / total_cells) * 100
            self.combat_stats['territory'][2] = (np.sum(next_grid == 2) / total_cells) * 100
            
            t1_score = np.sum(self.influence > 20.0)
            t2_score = np.sum(self.influence < -20.0)
            self.combat_stats['conquest_score'][1] = int(t1_score)
            self.combat_stats['conquest_score'][2] = int(t2_score)

        return self.get_battle_stats()

    def get_battle_stats(self) -> Dict:
        return {
            'step': self.step_count,
            'units_remaining': {
                1: int(np.sum(self.grid == 1)),
                2: int(np.sum(self.grid == 2))
            },
            'territory_control': self.combat_stats['territory'],
            'conquest_score': self.combat_stats['conquest_score'],
        }