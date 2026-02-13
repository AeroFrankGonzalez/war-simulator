from dataclasses import dataclass

@dataclass
class Unit:
    team_id: int
    health: int = 1