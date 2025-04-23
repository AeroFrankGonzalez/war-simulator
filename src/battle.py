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

        # --- 1. Process unit movements ---
        # Iterar sobre una copia de los diccionarios de unidades para evitar problemas si los equipos son eliminados
        # o si las unidades mueren durante la iteración (aunque el movimiento no mata, es buena práctica para el bucle general).
        for team_id, team_units in list(self.units.items()):
            # Iterar sobre una copia de la lista de unidades del equipo.
            for unit in list(team_units):
                # Asegurarse de que la unidad está viva antes de intentar moverla o procesarla.
                if unit.health > 0:
                    # Obtener el modificador de velocidad del terreno para la posición actual de la unidad.
                    # Las coordenadas de la unidad son flotantes, necesitamos convertirlas a enteros para indexar la matriz del terreno.
                    x, y = int(unit.position[0]), int(unit.position[1])

                    # Asegurarse de que estos índices enteros estén dentro de los límites válidos de la matriz del terreno.
                    # Esto maneja casos donde la unidad podría estar justo en el borde o fuera (si el movimiento la llevó allí).
                    x = max(0, min(x, self.terrain.width - 1))
                    y = max(0, min(y, self.terrain.height - 1))

                    terrain_mod = self.terrain.get_movement_modifier(x, y)

                    # --- INICIO DEL AJUSTE CLAVE para el TypeError ---
                    # Mover la unidad SOLAMENTE si tiene un target válido (es decir, no es None).
                    # Esta comprobación aquí dentro del método step de Battle es crucial
                    # porque este es el lugar donde unit.move es llamado.
                    if unit.target is not None:
                         # Llamar al método move de la unidad, pasando el target, modificador y límites del terreno.
                         unit.move(unit.target, terrain_mod, (self.terrain.width, self.terrain.height))
                    else:
                         # Si la unidad no tiene target asignado en este punto (por ejemplo, aún no se le ha dado uno
                         # o el comportamiento decidió no asignarle uno en este paso), simplemente se queda quieta.
                         pass # La unidad se queda quieta.
                    # --- FIN DEL AJUSTE CLAVE ---


        # --- 2. Process combat ---
        # Procesar el combate y determinar qué unidades mueren.
        casualties = []
        # Iterar sobre copias de las listas de unidades para manejar de forma segura la eliminación de unidades debido al combate.
        for team1_id, team1_units in list(self.units.items()):
            for unit1 in list(team1_units):
                 # Solo procesar combate para unidades que aún están vivas.
                 if unit1.health > 0:
                    # Iterar sobre los equipos enemigos.
                    for team2_id, team2_units in list(self.units.items()):
                        # Asegurarse de que no sea el mismo equipo.
                        if team1_id != team2_id:
                            # Iterar sobre las unidades enemigas (también copia).
                            for unit2 in list(team2_units):
                                # Solo procesar combate con unidades enemigas que aún están vivas.
                                # Y si unit1 está dentro del rango de contacto de unit2.
                                if unit2.health > 0 and unit1.is_in_contact_range(unit2, self.contact_radius):
                                    # unit1 ataca a unit2. unit2 intenta recibir daño.
                                    if unit2.take_damage():
                                        # Si unit2 muere, añadirla a la lista de bajas.
                                        casualties.append((team2_id, unit2))
                                        unit1.kills += 1 # Acreditar la baja a unit1.


        # --- 3. Remove casualties and update stats ---
        # Eliminar las unidades que murieron en este paso de la batalla.
        # Creamos un nuevo diccionario de unidades que solo contenga las unidades vivas.
        alive_units: Dict[int, List[Unit]] = {}
        # Iterar sobre los equipos y sus unidades actuales.
        for team_id, team_units in self.units.items():
            # Filtrar las unidades que tengan salud > 0 (las vivas).
            alive_units[team_id] = [unit for unit in team_units if unit.health > 0]
        # Actualizar el diccionario principal de unidades de la batalla con solo las unidades vivas.
        self.units = alive_units

        # Actualizar las estadísticas de combate basadas en la lista de bajas recolectada.
        for team_id, dead_unit in casualties:
             # Incrementar el contador de pérdidas para el equipo de la unidad que murió.
             # Usar .get() con valor por defecto 0 para manejar el primer registro para un equipo.
             if team_id not in self.combat_stats['losses']:
                self.combat_stats['losses'][team_id] = 0
             self.combat_stats['losses'][team_id] += 1


        # --- 4. Update territory control ---
        # Actualizar el estado de conquista del terreno.
        # Se necesitan las posiciones actuales de TODAS las unidades vivas para esto.
        unit_positions = {
            # Crear un diccionario mapeando team_id a una lista de tuplas (x, y) de las posiciones de las unidades.
            team_id: [(u.position[0], u.position[1]) for u in units]
            for team_id, units in self.units.items() # Iterar sobre el diccionario de unidades VIVAS.
        }
        # Llamar al método update_conquest del terreno con las posiciones de las unidades vivas.
        # El método update_conquest maneja la lógica de progreso y el mapa de conquista oficial.
        # Se usa un conquest_rate por defecto de 0.1 (puedes hacerlo configurable si lo necesitas).
        self.terrain.update_conquest(unit_positions, conquest_rate=0.1)

        # Actualizar las estadísticas de territorio conquistado basadas en el estado actual del terreno.
        # Iteramos sobre los IDs de equipo esperados (1 y 2) para asegurar que las estadísticas se muestren para ambos,
        # incluso si un equipo ya no tiene unidades vivas pero controlaba territorio.
        for team_id in [1, 2]: # Asumiendo IDs de equipo 1 y 2. Ajusta si usas otros IDs.
             # Obtener el porcentaje de conquista para el equipo, usando 0.0 como valor por defecto si no existe.
             self.combat_stats['territory'][team_id] = self.terrain.get_conquest_percentage(team_id)


        # --- Retornar las estadísticas actuales de la batalla ---
        # Se llama a get_battle_stats para compilar todas las estadísticas relevantes para este paso.
        return self.get_battle_stats()


    def get_battle_stats(self) -> Dict:
        """Return current battle statistics"""
        stats = {
            # Número total de pasos de simulación ejecutados.
            'step': self.step_count,
            # Conteo de unidades vivas restantes por equipo.
            'units_remaining': {team_id: len(units) for team_id, units in self.units.items()},
            # Porcentaje de terreno controlado oficialmente por cada equipo.
            'territory_control': self.combat_stats['territory'],
            # Conteo de unidades perdidas (muertas) por cada equipo.
            'casualties': self.combat_stats['losses'],
            # Conteo de unidades enemigas eliminadas por cada equipo.
            'total_kills': {
                # Sumar los contadores de kills de las unidades vivas restantes.
                # Nota: Esto solo cuenta las kills de unidades que SOBREVIVIERON al paso actual.
                # Si necesitas el total de kills incluyendo unidades que murieron,
                # la lógica de conteo de kills debería acumularse en combat_stats['kills']
                # cuando una unidad muere, en lugar de solo sumar las kills de unidades vivas.
                # Por ahora, sumamos las kills de las unidades VIVAS restantes.
                team_id: sum(unit.kills for unit in units)
                for team_id, units in self.units.items() # Iterar sobre el diccionario de unidades VIVAS.
            }
        }
        return stats