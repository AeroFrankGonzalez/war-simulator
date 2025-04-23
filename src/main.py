import sys
import time
import random # Importar el módulo random
import yaml
import numpy as np # Importar numpy
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
# Importa pygame aquí para inicializarlo al principio
import pygame

from terrain import Terrain, TerrainType # Asegúrate de que estas clases estén en terrain.py
from unit import Unit # Asegúrate de que la clase Unit esté en unit.py
from battle import Battle # Asegúrate de que la clase Battle esté en battle.py
from visualizer import Visualizer # Asegúrate de que la clase Visualizer esté en visualizer.py
from control_panel import ControlPanel # Asegúrate de que la clase ControlPanel esté en control_panel.py

class WarSimulator:
    def __init__(self):
        # Cargar la configuración inicial del archivo YAML
        self.load_config()

        # El visualizador se creará en init_simulation, no aquí.
        self.visualizer = None

        # Inicializar el estado de la simulación (terreno, batalla, unidades, visualizador)
        # Esto se llama tanto al inicio como al hacer Reset.
        # Asume que pygame.init() ya se llamó en main().
        self.init_simulation()

        # Estado de ejecución de la simulación (True cuando está corriendo, False cuando está pausada o detenida)
        self.running = False

        # Temporizador para controlar los pasos de la simulación en el bucle de eventos de PyQt.
        self.timer = QTimer()
        # Conectar la señal timeout del temporizador al método simulation_step.
        self.timer.timeout.connect(self.simulation_step)

        # Referencia al panel de control. Se asignará en la función main().
        self.control_panel = None


    def load_config(self, config_path: str = 'config.yaml'):
        """Load initial configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: config file not found at {config_path}")
            # Si no se encuentra el archivo de configuración, imprimir error y salir.
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            # Si el archivo de configuración tiene un error de formato YAML.
            sys.exit(1)


    def init_simulation(self):
        """Initialize or reset the simulation state (excluding Pygame init/quit)."""
        # Esta función se encarga de crear/reinicializar los objetos de simulación: terreno, batalla, unidades.
        # También crea o reinicializa la ventana de visualización de Pygame si es necesario.
        # Asume que pygame.init() ya se llamó en main().

        # Obtener el tamaño de la cuadrícula y el preset del terreno desde la configuración.
        grid_size = self.config.get('simulation', {}).get('grid_size', 50) # Default 50
        terrain_preset = self.config.get('terrain', {}).get('preset', 'valley') # Default 'valley'

        # Crear el terreno utilizando el preset y tamaño de la cuadrícula.
        self.terrain = Terrain.create_preset(terrain_preset, grid_size, grid_size)

        # Crear la batalla.
        contact_radius = self.config.get('terrain', {}).get('contact_radius', 1.0) # Default 1.0
        self.battle = Battle(self.terrain, contact_radius=contact_radius)

        # Crear o reiniciar el visualizador (ventana de Pygame).
        # Asumimos que pygame.init() ya se llamó en main().
        cell_size = self.config.get('simulation', {}).get('cell_size', 12) # Default 12
        if self.visualizer: # Si el visualizador ya existe (ej. en un Reset)
            self.visualizer.reset_display(grid_size, grid_size, cell_size) # Reinicia la ventana si es necesario (redimensiona)
        else: # Si es la primera vez que se crea
            self.visualizer = Visualizer(grid_size, grid_size, cell_size=cell_size) # Crea la instancia del visualizador

        # Crear las unidades iniciales para ambos equipos y añadirlas a la batalla.
        self.create_teams()

        # Opcional: Actualizar el estado inicial en el panel de control si ya existe.
        # Esto asegura que el panel muestra "Ready" al inicio o después de un Reset.
        if hasattr(self, 'control_panel') and self.control_panel:
             self.control_panel.update_status("Ready")


    def create_teams(self):
        """Create teams with current configuration and add them to the battle."""
        # Limpiar cualquier unidad existente antes de crear nuevas. Importante para el Reset.
        self.battle.units = {}

        # Obtener la configuración de los equipos desde self.config.
        # Usamos .get() para acceder de forma segura y proporcionar valores por defecto si faltan claves.
        team_configs = self.config.get('teams', {
            1: {'units': 20, 'speed': 1.0, 'health': 5, 'behavior': 'aggressive_advance'},
            2: {'units': 20, 'speed': 1.0, 'health': 5, 'behavior': 'aggressive_advance'},
        })


        for team_id in [1, 2]: # Procesar específicamente los equipos 1 y 2.
            team_config = team_configs.get(team_id, {
                'units': 20, 'speed': 1.0, 'health': 5, 'behavior': 'aggressive_advance'
            })

            num_units = team_config.get('units', 20)
            speed = team_config.get('speed', 1.0)
            health = team_config.get('health', 5)
            behavior = team_config.get('behavior', 'aggressive_advance')

            # --- Lógica para asignar posiciones iniciales ---
            # Basado en el lado del mapa (izquierda vs derecha) según el ID del equipo.
            start_area_width_factor = 0.3 # El área de inicio es el 30% del ancho del mapa en cada lado.
            start_area_width = self.terrain.width * start_area_width_factor

            if team_id == 1:
                # Equipo 1 inicia en el lado izquierdo del mapa.
                x_range = (0, start_area_width)
            else:
                # Equipo 2 inicia en el lado derecho del mapa.
                x_range = (self.terrain.width - start_area_width, self.terrain.width)

            initial_positions = []
            for _ in range(num_units):
                 # Generar una posición (x, y) aleatoria dentro del área de inicio designada.
                 pos_x = random.uniform(x_range[0], x_range[1])
                 pos_y = random.uniform(0, self.terrain.height) # La posición vertical puede ser en toda la altura del mapa.
                 initial_positions.append((pos_x, pos_y))
            # --- Fin de la lógica de posiciones iniciales ---


            # Crear las instancias de Unit y añadirlas al objeto Battle.
            for i in range(num_units):
                unit = Unit(
                    team_id=team_id,
                    position=initial_positions[i],
                    health=health,
                    movement_speed=speed,
                    behavior=behavior # Asignar el comportamiento configurado a la unidad.
                )
                self.battle.add_unit(unit)

            # No asignamos un target inicial aquí. La lógica en simulation_step se encargará de esto
            # basándose en el comportamiento de cada unidad.


    def simulation_step(self):
        """Execute one step of the battle simulation."""
        # Esta función se llama repetidamente por el QTimer cuando la simulación está corriendo.

        # Si la simulación no está marcada como corriendo (está pausada o detenida), no hacer nada.
        if not self.running:
            return

        # Obtener los límites del terreno (ancho y alto) para pasarlos al método de movimiento de las unidades.
        terrain_bounds = (self.terrain.width, self.terrain.height)
        # Obtener una referencia al diccionario de todas las unidades en la batalla.
        all_units = self.battle.units

        # --- Lógica de comportamiento y selección de target para cada unidad ---
        # Iteramos sobre una copia del diccionario de unidades para evitar problemas si los equipos se quedan sin unidades
        # o si las unidades son eliminadas durante el bucle (por ejemplo, si se implementa muerte natural o eventos).
        for team_id, team_units in list(all_units.items()):
            # Iteramos sobre una copia de la lista de unidades de cada equipo.
            # Esto es crucial porque las unidades pueden ser eliminadas de la lista original
            # en el método battle.step() (durante el procesamiento del combate).
            for unit in list(team_units):
                 # Si la unidad ya está muerta (su salud es 0 o menos), pasar a la siguiente unidad.
                 if unit.health <= 0:
                     continue # Saltar el procesamiento de esta unidad si ya está muerta.


                 # Determinar si la unidad necesita que se le asigne un nuevo target en este paso de simulación.
                 # Un nuevo target es necesario si la unidad no tiene target actualmente (unit.target es None),
                 # si alcanzó su target anterior (el método unit.move establece unit.target a None al llegar),
                 # o si se cumple una probabilidad aleatoria de recalcular el target.
                 needs_new_target = False
                 if unit.target is None: # Si no tiene target asignado.
                     needs_new_target = True
                 elif random.random() < self.config.get('units', {}).get('target_recalculation_probability', 0.02): # Si se cumple la probabilidad de recalcular.
                     needs_new_target = True # Usar .get() con un valor por defecto seguro (0.02)


                 # Si se determina que se necesita un nuevo target, asignarlo basándose en el comportamiento configurado de la unidad.
                 if needs_new_target:
                     if unit.behavior == 'aggressive_advance':
                         # Comportamiento "Avance Agresivo": Moverse hacia un punto aleatorio en el lado del mapa opuesto al equipo.
                         if unit.team_id == 1: # Equipo 1 (Rojo) avanza hacia el lado derecho (donde empieza el Equipo 2).
                             target_x = random.uniform(self.terrain.width * 0.7, self.terrain.width)
                         else: # Equipo 2 (Azul) avanza hacia el lado izquierdo (donde empieza el Equipo 1).
                             target_x = random.uniform(0, self.terrain.width * 0.3)
                         target_y = random.uniform(0, self.terrain.height) # La posición vertical puede ser en cualquier parte.
                         unit.target = (target_x, target_y) # Asignar el nuevo target a la unidad.

                     elif unit.behavior == 'seek_and_destroy':
                         # Comportamiento "Buscar y Destruir": Buscar la unidad enemiga viva más cercana y moverse hacia ella.
                         nearest_enemy = unit.find_nearest_enemy(all_units) # Llamar al método de la unidad para encontrar al enemigo más cercano.
                         if nearest_enemy:
                             # Si se encuentra un enemigo (no es None), su posición actual es el nuevo target.
                             unit.target = nearest_enemy.position
                         else:
                             # Si no se encuentran unidades enemigas vivas en el mapa, asignar un target de "fallback".
                             # Por ejemplo, hacer que avance agresivamente hacia el lado enemigo como alternativa, en lugar de quedarse quieta.
                             # Esto evita que las unidades dejen de moverse si eliminan a todos los enemigos cercanos.
                             if unit.team_id == 1: target_x = random.uniform(self.terrain.width * 0.7, self.terrain.width)
                             else: target_x = random.uniform(0, self.terrain.width * 0.3)
                             target_y = random.uniform(0, self.terrain.height)
                             unit.target = (target_x, target_y) # Asignar el target de fallback.
                             # Puedes añadir un mensaje de depuración aquí si quieres ver cuándo las unidades cambian a este fallback.
                             # print(f"DEBUG: Unit {unit.team_id} at {unit.position} switching to fallback target (aggressive advance) as no enemies found.")


                     elif unit.behavior == 'random_walk':
                          # Comportamiento "Paseo Aleatorio": Moverse a un punto aleatorio dentro de un radio local alrededor de la posición actual.
                          # Esto simula exploración o dispersión.
                          random_target_radius = min(self.terrain.width, self.terrain.height) * 0.2 # Definir el radio máximo para el nuevo target aleatorio.
                          current_pos = np.array(unit.position) # Obtener la posición actual de la unidad como un array de numpy.

                          # Generar un vector de desplazamiento aleatorio dentro del radio definido.
                          angle = random.uniform(0, 2 * np.pi) # Ángulo aleatorio en radianes.
                          distance = random.uniform(0, random_target_radius) # Distancia aleatoria desde la posición actual.
                          target_offset = np.array([distance * np.cos(angle), distance * np.sin(angle)]) # Calcular el desplazamiento (delta x, delta y).

                          new_target_pos_raw = current_pos + target_offset # Calcular la posible nueva posición target (sin comprobar límites aún).

                          # Asegurarse de que la nueva posición target aleatoria calculada esté dentro de los límites del mapa.
                          # Usar max(0.0, ...) y min(map_dim - 0.1, ...) para mantenerse ligeramente dentro de los bordes
                          # y evitar targets exactamente en el borde que podrían causar problemas con el índice de la matriz del terreno.
                          target_x = max(0.0, min(self.terrain.width - 0.1 , new_target_pos_raw[0]))
                          target_y = max(0.0, min(self.terrain.height - 0.1, new_target_pos_raw[1]))

                          unit.target = (target_x, target_y) # Asignar el nuevo target aleatorio dentro de los límites.

                     # Añade bloques 'elif unit.behavior == ...' aquí para otros comportamientos si los implementas.


                 # --- Mover la unidad SOLAMENTE si tiene un target válido (NO es None) ---
                 # Esta es la comprobación CRÍTICA agregada para evitar el `TypeError` "NoneType and float".
                 # Se realiza justo antes de llamar al método unit.move().
                 if unit.target is not None:
                     # Obtener el modificador de velocidad del terreno para la posición actual de la unidad.
                     # Convertir las coordenadas de la unidad (flotantes) a enteros para indexar la matriz del terreno.
                     x_int, y_int = int(unit.position[0]), int(unit.position[1])

                     # Asegurarse de que estos índices enteros estén dentro de los límites válidos de la matriz del terreno.
                     # Esto es importante para evitar errores de "IndexError: index out of bounds" si la unidad está exactamente en el borde.
                     x_int = max(0, min(x_int, self.terrain.width - 1))
                     y_int = max(0, min(y_int, self.terrain.height - 1))

                     # Obtener el modificador del terreno llamando al método del objeto terrain.
                     terrain_mod = self.terrain.get_movement_modifier(x_int, y_int)

                     # Llamar al método move de la unidad, pasando el target, el modificador de velocidad del terreno y los límites del terreno.
                     unit.move(unit.target, terrain_mod, terrain_bounds)
                 else:
                      # Si, después de toda la lógica de asignación de target en este paso, unit.target sigue siendo None,
                      # la unidad no tiene un destino válido para este paso y simplemente se queda quieta.
                      # Puedes descomentar la siguiente línea para depurar si sospechas que las unidades no están recibiendo targets.
                      # print(f"DEBUG: Unit {unit.team_id} at {unit.position} has no target assigned in this step.")
                      pass # La unidad no se mueve en este paso si no tiene target.

        # --- Fin de la lógica de comportamiento y selección de target ---

        # Ejecutar un paso de la lógica de batalla (combate, actualización de conquista, etc.).
        # Este método llama a Terrain.update_conquest() internamente.
        battle_stats = self.battle.step()

        # Actualizar la visualización para mostrar el estado actual de la batalla y el terreno.
        # Se pasa el objeto battle al visualizador para que tenga acceso a todos los datos necesarios.
        # Si el método update del visualizador devuelve False (por ejemplo, porque se cerró la ventana de Pygame),
        # indicamos que la simulación debe detenerse.
        if not self.visualizer.update(self.battle):
            self.stop_simulation() # Detener el temporizador y marcar running=False.
            # Si el panel de control existe, actualizar su estado para reflejar que la simulación terminó porque se cerró la ventana.
            if hasattr(self, 'control_panel') and self.control_panel:
                 self.control_panel.update_status("Simulation Ended (Window Closed)")
            # Salir de la función simulation_step para detener el procesamiento de este paso.
            return


        # --- Comprobar condiciones de victoria ---
        # Obtener la lista de IDs de los equipos que aún tienen unidades vivas en la batalla.
        remaining_teams = [team_id for team_id, units in self.battle.units.items() if units]

        # Condición de victoria 1: Por conquista de terreno (REQ-CONTROL-6.2).
        # Necesitas definir un umbral de porcentaje de conquista para ganar.
        # Puedes añadir un parámetro 'conquest_percentage' en una sección 'victory' de tu config.yaml
        # o usar un valor fijo aquí. Usaremos un valor fijo temporal de 70%.
        conquest_win_threshold = 70.0
        # Intenta leer el umbral de la configuración si existe (ideal para hacerlo configurable):
        # conquest_win_threshold = self.config.get('victory', {}).get('conquest_percentage', 70.0)


        # Verificar si algún equipo ha alcanzado o superado el umbral de conquista.
        winner_by_conquest = None
        # Iterar sobre los IDs de los equipos que existen en la configuración inicial (típicamente 1 y 2).
        # Esto asegura que revisamos el porcentaje de conquista para ambos equipos,
        # incluso si uno ya no tiene unidades vivas pero controlaba territorio.
        for team_id in self.config.get('teams', {}).keys(): # Usamos .get({}, {}) para seguridad si 'teams' falta en config
            # Obtener el porcentaje de conquista para este equipo desde las estadísticas de batalla.
            # Usar .get() con valor por defecto 0.0 si el equipo no tiene estadísticas de territorio aún.
            conquest_percentage = battle_stats['territory_control'].get(team_id, 0.0)
            if conquest_percentage >= conquest_win_threshold:
                 # Si el porcentaje de conquista es mayor o igual al umbral, este equipo es el ganador por conquista.
                 winner_by_conquest = team_id
                 break # Encontramos un ganador por conquista, salimos del bucle de verificación.


        # Condición de victoria 2: Por aniquilación del equipo enemigo (REQ-CONTROL-6.1).
        winner_by_annihilation = None
        if len(remaining_teams) == 1:
             # Si solo queda exactamente un equipo con unidades vivas en el mapa, ese equipo gana por aniquilación.
             winner_by_annihilation = remaining_teams[0]
        elif len(remaining_teams) == 0:
             # Si no queda ningún equipo con unidades vivas, esto resulta en un empate total (ambos aniquilados).
             pass # No hay un ganador por aniquilación en este caso, se maneja más abajo como un posible empate global.


        # Determinar el resultado final de la simulación y si ha terminado.
        simulation_ended = False
        win_message = "" # Mensaje que se mostrará al final.

        if winner_by_conquest is not None:
            # Si se encontró un ganador por conquista, la simulación termina.
            simulation_ended = True
            win_message = f"Team {winner_by_conquest} wins by conquest!"
        elif winner_by_annihilation is not None:
             # Si se encontró un ganador por aniquilación (y no hubo victoria por conquista antes), la simulación termina.
             simulation_ended = True
             win_message = f"Team {winner_by_annihilation} wins by annihilation!"
        elif len(remaining_teams) == 0:
             # Si no queda ningún equipo con unidades vivas (y no hubo victoria por conquista), es un empate.
             simulation_ended = True
             win_message = "Draw - all units destroyed!"

        # Si la simulación ha terminado por alguna de las condiciones...
        if simulation_ended:
             # Detener el temporizador y marcar running=False.
             # La función stop_simulation ahora NO llama a pygame.quit().
             self.stop_simulation()
             print("\n--- Simulation Ended ---") # Imprimir un separador en la consola.
             print(win_message) # Imprimir el mensaje final (victoria/empate).

             # Imprimir las estadísticas finales de la batalla.
             print(f"Final Territory control:")
             # Iterar por los equipos de la configuración inicial para asegurar que se muestran ambos, incluso si uno tiene 0%.
             for team_id in self.config.get('teams', {}).keys():
                 # Usar .get() con valor por defecto 0.0% para mostrar 0.0% si un equipo no conquistó nada o fue aniquilado.
                 print(f"  Team {team_id}: {battle_stats.get('territory_control', {}).get(team_id, 0.0):.1f}%")

             print(f"Final Total kills:")
             # Usar .get() con valor por defecto 0 kills si un equipo no tuvo kills o fue aniquilado.
             for team_id in self.config.get('teams', {}).keys():
                  total_kills = battle_stats.get('total_kills', {}).get(team_id, 0)
                  print(f"  Team {team_id}: {total_kills}")

             print(f"Final Casualties:")
             # Usar .get() con valor por defecto 0 bajas si un equipo no tuvo bajas o no tenía unidades.
             for team_id in self.config.get('teams', {}).keys():
                  print(f"  Team {team_id}: {battle_stats.get('casualties', {}).get(team_id, 0)}")

             print("------------------------") # Imprimir un separador final.

             # Si el panel de control existe, actualizar su estado con el mensaje final.
             if hasattr(self, 'control_panel') and self.control_panel:
                  self.control_panel.update_status(win_message)

        # La función simulation_step termina aquí. Si la simulación no ha terminado,
        # el temporizador volverá a dispararse para ejecutar el siguiente paso en el tiempo configurado.


    def update_params(self, params: dict):
        """Update simulation parameters from control panel and reset simulation."""
        # Este método es llamado por el panel de control cuando los parámetros cambian.

        # Actualizar la configuración interna de la simulación con los parámetros recibidos del panel.
        # Usamos .get() para acceder de forma segura y proporcionar valores por defecto.

        # Parámetros generales de simulación, terreno y unidades.
        sim_config = self.config.get('simulation', {})
        terrain_config = self.config.get('terrain', {})
        units_config = self.config.get('units', {})

        sim_config['grid_size'] = params.get('grid_size', sim_config.get('grid_size', 50))
        sim_config['cell_size'] = params.get('cell_size', sim_config.get('cell_size', 12))
        sim_config['simulation_speed'] = params.get('simulation_speed', sim_config.get('simulation_speed', 0.05))

        terrain_config['preset'] = params.get('terrain_preset', terrain_config.get('preset', 'valley'))
        terrain_config['contact_radius'] = params.get('contact_radius', terrain_config.get('contact_radius', 1.0))

        # target_recalculation_probability no está en el panel de control actual, pero se mantiene en config
        # units_config['target_recalculation_probability'] = params.get('target_recalculation_probability', units_config.get('target_recalculation_probability', 0.02))


        # Actualizar la configuración de los equipos.
        teams_params = params.get('teams', {})
        for team_id in [1, 2]: # Procesar específicamente los equipos 1 y 2.
            team_config = self.config.get('teams', {}).get(team_id, {}) # Obtener config existente o inicializar vacío
            team_params = teams_params.get(team_id, {}) # Obtener parámetros para este equipo desde el panel

            # Actualizar parámetros específicos del equipo, usando fallbacks.
            team_config['units'] = team_params.get('units', team_config.get('units', 20))
            team_config['speed'] = team_params.get('speed', team_config.get('speed', 1.0))
            team_config['health'] = team_params.get('health', team_config.get('health', 5))
            # behavior es nuevo en el panel, usar valor por defecto si no está presente
            team_config['behavior'] = team_params.get('behavior', team_config.get('behavior', 'aggressive_advance'))

            self.config['teams'][team_id] = team_config # Guardar la configuración actualizada para el equipo


        # Asegurarse de que las claves principales existan en self.config después de actualizar (si no existían antes).
        self.config['simulation'] = sim_config
        self.config['terrain'] = terrain_config
        self.config['units'] = units_config


        # Actualizar el intervalo del temporizador con la nueva velocidad de simulación.
        # Esto puede ocurrir incluso si la simulación está pausada o detenida.
        self.timer.setInterval(int(self.config['simulation']['simulation_speed'] * 1000))

        # Después de actualizar los parámetros, reiniciar la simulación al estado inicial con la nueva configuración.
        self.reset_simulation()


    def handle_control(self, command: str):
        """Handle control commands received from the control panel."""
        # Obtener una referencia segura al panel de control.
        cp = getattr(self, 'control_panel', None)

        if command == "start":
            self.start_simulation() # Iniciar o reanudar la simulación.
            if cp: cp.update_status("Running") # Actualizar el estado en el panel.
        elif command == "pause":
            self.pause_simulation() # Pausar la simulación.
            if cp: cp.update_status("Paused") # Actualizar el estado en el panel.
        elif command == "reset":
            self.reset_simulation() # Reiniciar la simulación al estado inicial.
            # El estado "Ready" se establece dentro de reset_simulation.
        elif command == "end":
            self.end_simulation() # Terminar la simulación y salir de la aplicación.
            # La aplicación se cierra dentro de end_simulation.


    def start_simulation(self):
        """Start or resume the simulation timer."""
        # Solo iniciar el temporizador si la simulación no está ya marcada como corriendo.
        if not self.running:
            self.running = True
            # Asegurarse de que el visualizador está inicializado antes de que empiece el timer.
            # Esto ya lo asegura init_simulation.
            if self.visualizer is None:
                 # Esto no debería pasar con el flujo actual, pero como seguridad...
                 print("Warning: Visualizer not initialized when starting simulation. Attempting to initialize.")
                 self.init_simulation() # Intentar inicializarlo si por alguna razón no lo está.

            # Iniciar el temporizador. Disparará el evento timeout repetidamente.
            self.timer.start(int(self.config['simulation']['simulation_speed'] * 1000))
            # El estado del panel se actualiza en handle_control.


    def pause_simulation(self):
        """Pause the simulation timer."""
        # Solo detener el temporizador si la simulación está marcada como corriendo.
        if self.running:
            self.running = False
            self.timer.stop() # Detener el temporizador.
            # El estado del panel se actualiza en handle_control.


    def stop_simulation(self):
        """Stop the simulation timer and set running to False (does NOT quit Pygame)."""
        # Detiene el temporizador y marca el estado de la simulación como no corriendo.
        # Es llamada por pause_simulation, reset_simulation, end_simulation, y simulation_step (en caso de cierre de ventana o fin de partida).
        self.running = False
        self.timer.stop() # Detener el temporizador.

        # Importante: Esta función NO llama a pygame.quit().
        # pygame.quit() solo se llama UNA VEZ al final de la vida de la aplicación, desde end_simulation.


    def reset_simulation(self):
        """Reset the simulation to its initial state based on current configuration."""
        # Primero, asegurarse de que la simulación actual está detenida.
        # stop_simulation NO cierra Pygame.
        self.stop_simulation()
        # Luego, reinicializar todos los objetos de simulación y la ventana de visualización.
        # init_simulation llamará a visualizer.reset_display o creará un nuevo visualizador.
        self.init_simulation()
        # El estado "Ready" en el panel se establece dentro de init_simulation.


    def end_simulation(self):
        """End the simulation entirely, quit Pygame, close panel, and exit application."""
        # Detener la simulación si está corriendo.
        self.stop_simulation()

        # Si el visualizador existe, llamar a su método para cerrar Pygame.
        # Este método contiene la única llamada a pygame.quit().
        if hasattr(self, 'visualizer') and self.visualizer:
             self.visualizer.quit_pygame()

        # Si el panel de control existe, cerrarlo.
        if hasattr(self, 'control_panel') and self.control_panel:
             self.control_panel.close()

        # Finalmente, salir de la aplicación de PyQt.
        # Esto termina el bucle de eventos de QApplication.
        QApplication.quit()


# --- Función principal para iniciar la aplicación ---
def main():
    # 1. Inicializar Pygame PRIMERO.
    # Esto debe hacerse una sola vez al inicio de la aplicación, antes de crear cualquier objeto que use Pygame.
    pygame.init()
    # Nota: pygamge.init() puede ser llamado varias veces, pero solo se inicializa la primera vez.
    # Sin embargo, llamarlo solo una vez explícitamente al inicio es más claro.


    # 2. Inicializar la aplicación de PyQt.
    app = QApplication(sys.argv)

    # 3. Crear la instancia principal del simulador.
    simulator = WarSimulator() # Llama a __init__, que a su vez llama a init_simulation y crea el visualizador (que usa Pygame).

    # 4. Crear y mostrar el panel de control de la UI.
    control_panel = ControlPanel()
    control_panel.show()
    # Guardar una referencia al panel en el objeto simulador.
    simulator.control_panel = control_panel

    # 5. Conectar las señales del panel de control (cambios en parámetros, clics en botones)
    # a los métodos correspondientes en el objeto simulador.
    control_panel.params_changed.connect(simulator.update_params)
    control_panel.simulation_control.connect(simulator.handle_control)

    # 6. La simulación está ahora en estado "Ready".
    # Esperará a que el usuario haga click en "Start" en el panel de control para comenzar.
    # No llamamos a simulator.start_simulation() aquí al inicio.

    # 7. Iniciar el bucle principal de eventos de PyQt.
    # app.exec_() inicia el bucle de eventos. La aplicación se mantendrá corriendo aquí,
    # procesando eventos de UI, temporizadores, etc., hasta que QApplication.quit() sea llamado.
    sys.exit(app.exec_())

# Bloque principal para ejecutar la función main() cuando el script se corre directamente.
if __name__ == "__main__":
    main()