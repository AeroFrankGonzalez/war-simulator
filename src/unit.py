# unit.py

from dataclasses import dataclass, field # Importa field además de dataclass
from typing import Tuple, Optional, Dict, List # Importa List
import numpy as np # Importa numpy

@dataclass
class Unit:
    """Represents a single unit in the battle simulation."""
    team_id: int # El ID del equipo al que pertenece la unidad (ej. 1 o 2).
    position: Tuple[float, float] # La posición actual de la unidad en el terreno (coordenadas flotantes).
    health: int = 5 # La salud actual o resistencia al contacto de la unidad (inicialmente 5).
    movement_speed: float = 1.0 # La velocidad base de movimiento de la unidad.
    kills: int = 0 # Contador del número de unidades enemigas que esta unidad ha eliminado.
    distance_moved: float = 0.0 # Distancia total que esta unidad ha recorrido.
    target: Optional[Tuple[float, float]] = None # El target actual de la unidad (una posición o None si no tiene target).
    last_direction: Optional[Tuple[float, float]] = None # La última dirección de movimiento de la unidad, usada para rebotes.
    behavior: str = 'aggressive_advance' # El tipo de comportamiento estratégico que sigue esta unidad (ej. 'aggressive_advance', 'seek_and_destroy', 'random_walk').


    def move(self, target: Tuple[float, float], terrain_modifier: float = 1.0, terrain_bounds: Optional[Tuple[float, float]] = None) -> None:
        """
        Moves the unit towards the target position.
        Considers terrain effects on speed and handles boundary collisions.
        Requires target to be a valid tuple, not None.
        """
        # Calcular el vector de dirección desde la posición actual al target.
        # np.array(target) es seguro porque se llama después de comprobar que target is not None.
        direction = np.array(target) - np.array(self.position)
        # Calcular la distancia al target.
        distance = np.linalg.norm(direction)

        # Definir un pequeño umbral para considerar que el target ha sido "alcanzado".
        # Si la unidad está muy cerca del target (menos que este umbral), se considera alcanzado.
        # Usar un umbral relativo a la velocidad puede hacer que la detección sea más consistente.
        target_threshold = 0.5 * self.movement_speed * terrain_modifier # Umbral dinámico basado en velocidad y terreno


        if distance > target_threshold: # Solo moverse si no está ya muy cerca del target.
            # Normalizar el vector de dirección para obtener solo la dirección.
            normalized_direction = direction / distance
            # Calcular la velocidad efectiva de movimiento considerando la velocidad base y el modificador del terreno.
            actual_speed = self.movement_speed * terrain_modifier
            # Calcular el vector de movimiento para este paso.
            movement = normalized_direction * actual_speed
            # Calcular la nueva posición potencial.
            new_position = np.array(self.position) + movement

            # --- Manejo de colisiones con los límites del terreno ---
            if terrain_bounds:
                width, height = terrain_bounds
                # Comprobar si la nueva posición estaría fuera de los límites.
                if (new_position[0] < 0 or new_position[0] >= width or
                    new_position[1] < 0 or new_position[1] >= height):

                    # Lógica simple de "rebote" o cambio de dirección al golpear un límite.
                    # Revertir la componente de movimiento que cruzó el límite.
                    if new_position[0] < 0 or new_position[0] >= width:
                        movement[0] *= -1 # Revertir movimiento en X

                    if new_position[1] < 0 or new_position[1] >= height:
                        movement[1] *= -1 # Revertir movimiento en Y

                    # Calcular la nueva posición basándose en el movimiento "rebotado".
                    new_position = np.array(self.position) + movement

                    # Opcional: Asegurar que la unidad se mantenga estrictamente dentro de los límites después del "rebote".
                    # Esto puede evitar que la unidad se quede atascada si el rebote no la aleja lo suficiente.
                    new_position[0] = np.clip(new_position[0], 0.1, width - 0.1) # Clamping a 0.1 unidades del borde
                    new_position[1] = np.clip(new_position[1], 0.1, height - 0.1)

                    # Actualizar la última dirección basándose en el movimiento rebotado (antes del clipping).
                    # Esto puede ser útil si la lógica de comportamiento la usa.
                    # Asegurarse de que la velocidad actual no sea cero para evitar división por cero.
                    if actual_speed > 1e-6: # Usar un pequeño epsilon para la comparación de flotantes
                         self.last_direction = tuple(movement / actual_speed)
                    else:
                         self.last_direction = (0.0, 0.0) # Dirección nula si la velocidad es ~0

                else: # Si la nueva posición está dentro de los límites, aplicarla directamente.
                    # Actualizar la última dirección basándose en el movimiento normal.
                    # Asegurarse de que la velocidad actual no sea cero.
                    if actual_speed > 1e-6:
                         self.last_direction = tuple(movement / actual_speed)
                    else:
                         self.last_direction = (0.0, 0.0)

                    # Actualizar la distancia total movida (opcional para estadísticas).
                    self.distance_moved += actual_speed
                    # Aplicar la nueva posición.
                    self.position = tuple(new_position)

            else: # Si no se proporcionan límites del terreno, moverse sin comprobar bordes.
                 if actual_speed > 1e-6:
                      self.last_direction = tuple(movement / actual_speed)
                 else:
                      self.last_direction = (0.0, 0.0)
                 self.distance_moved += actual_speed
                 self.position = tuple(new_position)

        else:
             # Si la unidad está muy cerca del target (dentro del umbral), considerar que el target ha sido alcanzado.
             # Limpiar el target para que la lógica en simulation_step le asigne uno nuevo.
             self.target = None
             # Opcional: Ajustar la posición para que sea exactamente el target si está muy cerca
             # self.position = target


    def take_damage(self) -> bool:
        """
        Unit takes 1 point of damage.
        Decreases the unit's health by 1.
        Returns True if the unit dies (health drops to 0 or less), False otherwise.
        """
        self.health -= 1
        # Devolver True si la salud es menor o igual a 0, indicando que la unidad ha muerto.
        return self.health <= 0


    def is_in_contact_range(self, other_unit: 'Unit', contact_radius: float) -> bool:
        """
        Checks if this unit is within contact range of another unit.
        Contact occurs if the distance between unit centers is less than or equal to the contact radius.
        """
        # Calcular la distancia euclidiana entre la posición de esta unidad y la otra unidad.
        distance = np.linalg.norm(
            np.array(self.position) - np.array(other_unit.position)
        )
        # Comparar la distancia con el radio de contacto para determinar si hay contacto.
        return distance <= contact_radius


    def find_nearest_enemy(self, all_units: Dict[int, list['Unit']]) -> Optional['Unit']:
        """
        Finds the nearest living enemy unit to this unit.
        Args:
            all_units: A dictionary mapping team_id to a list of all units for that team.
        Returns:
            The nearest living enemy Unit object, or None if no living enemies are found.
        """
        # Determinar el ID del equipo enemigo.
        enemy_team_id = 1 if self.team_id == 2 else 2
        # Obtener la lista de unidades del equipo enemigo (usando .get() para manejar si el equipo ya no existe).
        enemy_units = all_units.get(enemy_team_id, [])

        # Si no hay unidades en la lista del equipo enemigo, no hay enemigos que encontrar.
        if not enemy_units:
            return None

        nearest_enemy = None
        min_distance = float('inf') # Inicializar la distancia mínima como infinito.

        # Iterar a través de todas las unidades enemigas.
        for enemy_unit in enemy_units:
            # Solo considerar unidades enemigas que estén vivas.
            if enemy_unit.health > 0:
                # Calcular la distancia a esta unidad enemiga.
                distance = np.linalg.norm(np.array(self.position) - np.array(enemy_unit.position))
                # Si esta unidad enemiga está más cerca que la distancia mínima encontrada hasta ahora...
                if distance < min_distance:
                    min_distance = distance # Actualizar la distancia mínima.
                    nearest_enemy = enemy_unit # Actualizar la referencia a la unidad enemiga más cercana.

        # Devolver la unidad enemiga más cercana encontrada, o None si no se encontró ninguna (ej. si todas estaban muertas).
        return nearest_enemy