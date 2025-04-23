import pygame
import numpy as np
from battle import Battle # Asegúrate de que la clase Battle esté en battle.py
from terrain import Terrain, TerrainType # Asegúrate de que Terrain y TerrainType estén en terrain.py
from typing import Dict, Tuple

class Visualizer:
    def __init__(self, width: int, height: int, cell_size: int = 10):
        """
        Initializes the visualizer. Assumes pygame.init() has been called BEFOREHAND.
        """
        # Importante: NO llamar pygame.init() aquí. Se llama una vez al inicio en main.py.

        self.cell_size = cell_size # Tamaño de cada celda en píxeles.
        self.grid_width = width # Ancho de la cuadrícula del terreno en celdas.
        self.grid_height = height # Alto de la cuadrícula del terreno en celdas.
        # Calcular el tamaño de la ventana de Pygame en píxeles.
        self.width = self.grid_width * self.cell_size
        self.height = self.grid_height * self.cell_size

        # Configurar la ventana de visualización de Pygame.
        # Esto requiere que Pygame esté inicializado.
        try:
            # Intenta establecer el modo de visualización.
            # Se añade espacio extra a la derecha para el panel de estadísticas.
            self.screen = pygame.display.set_mode((self.width + 200, self.height))
            # Establecer el título de la ventana.
            pygame.display.set_caption("War Simulator")
        except pygame.error as e:
            # Si ocurre un error al inicializar la pantalla de Pygame (ej. drivers, o si pygame.init() falló).
            print(f"Error initializing Pygame display: {e}")
            # En caso de fallo crítico al crear la pantalla, probablemente la aplicación no pueda continuar.
            # Intenta limpiar Pygame si algo se inició antes de fallar.
            if pygame.get_init(): # Verifica si Pygame llegó a inicializarse.
                 pygame.quit() # Intenta cerrar Pygame.
            # Re-lanzar el error para que la función que llamó a __init__ (en main.py) pueda manejarlo o el programa termine.
            raise


        # Definiciones de colores utilizados para dibujar.
        self.colors = {
            # Colores base para los diferentes tipos de terreno.
            'terrain_types': {
                TerrainType.GRASS: pygame.Color(124, 252, 0),   # Lawn Green
                TerrainType.WATER: pygame.Color(0, 191, 255),   # Deep Sky Blue
                TerrainType.FOREST: pygame.Color(34, 139, 34), # Forest Green
                TerrainType.SAND: pygame.Color(245, 222, 179),  # Wheat
                TerrainType.MOUNTAIN: pygame.Color(139, 69, 19), # Saddle Brown
                # Puedes añadir colores para otros tipos de terreno aquí (usando las constantes de TerrainType).
            },
            # Factores para aplicar variaciones de color basadas en la altura y densidad dentro de cada tipo de terreno.
            'variation': {
                'height_shade_factor': 0.25, # Cuánto oscurecer/aclarar el color base por la altura (0 a 1).
                'density_factor': 0.4     # Cuánto aplicar la influencia de la densidad como opacidad o tinte (0 a 1).
            },
            # Colores para los equipos de unidades.
            'units': {
                1: pygame.Color(255, 0, 0),    # Team 1 (Red)
                2: pygame.Color(0, 0, 255)     # Team 2 (Blue)
                # Añade colores para otros equipos si implementas más de 2.
            },
            # Colores para el área de terreno que ha sido oficialmente conquistada por un equipo.
            'territory': {
                1: pygame.Color(255, 150, 150),  # Rojo claro/medio para territorio del Equipo 1.
                2: pygame.Color(150, 150, 255)   # Azul claro/medio para territorio del Equipo 2.
            },
             # Estilo para el indicador visual de áreas bajo influencia activa o contienda (donde hay unidades).
             'contested_indicator': {
                'border_color': (255, 255, 0), # Color del borde (ej. Amarillo para resaltar).
                'overlay_alpha': 80           # Opacidad del overlay semi-transparente (0 a 255).
            }
        }
        # Inicializar el sistema de fuentes de Pygame.
        # Esto debe ocurrir DESPUÉS de pygame.init() (que se llama en main.py).
        # Es seguro llamarlo en __init__ porque __init__ se ejecuta después de la llamada a pygame.init() en main.
        pygame.font.init()
        # Crear un objeto fuente para dibujar texto (ej. en el panel de estadísticas).
        self.font = pygame.font.SysFont(None, 24) # Usa la fuente por defecto, tamaño 24.


    def draw_terrain(self, terrain: Terrain) -> None:
        """Draw terrain features including type, height, density, and territory control."""
        # Obtener los mapas de datos del terreno para dibujar.
        terrain_type_map = terrain.get_terrain_type_map() # Mapa de tipos de terreno (ej. GRASS, WATER).
        conquest_map = terrain.conquest_map # Mapa de conquista oficial (0, 1, 2).
        conquest_progress = terrain.conquest_progress # Mapa de progreso de conquista (0.0 a 1.0).
        control_points = terrain.control_points # Mapa de control inmediato (quién influye ahora, basado en unidades).

        # Iterar por cada celda del terreno.
        for y in range(terrain.height):
            for x in range(terrain.width):
                # Calcular el rectángulo en la pantalla de Pygame para esta celda.
                rect = pygame.Rect(
                    x * self.cell_size, # Posición X en píxeles.
                    y * self.cell_size, # Posición Y en píxeles.
                    self.cell_size, # Ancho en píxeles (tamaño de la celda).
                    self.cell_size # Alto en píxeles (tamaño de la celda).
                )

                # --- 1. Draw Base Terrain (with height/density variation) ---
                # Dibujar el color base del terreno con variaciones según altura y densidad.

                # Obtener el tipo de terreno de la celda actual.
                terrain_type = terrain_type_map[y, x]
                # Obtener el color base para este tipo de terreno. Usar color de GRASS si el tipo no está definido.
                base_color = self.colors['terrain_types'].get(terrain_type, self.colors['terrain_types'][TerrainType.GRASS])

                # Aplicar sombreado basado en la altura. Oscurecer el color base según el valor de altura.
                height_value = terrain.height_map[y, x] # Valor de altura (0.0 a 1.0).
                shade_factor = height_value * self.colors['variation']['height_shade_factor'] # Factor de sombreado (mayor altura -> más sombreado).
                shaded_color = (
                    int(base_color[0] * (1 - shade_factor)),
                    int(base_color[1] * (1 - shade_factor)),
                    int(base_color[2] * (1 - shade_factor))
                )
                # Asegurarse de que los valores de color resultantes estén dentro del rango válido (0-255).
                shaded_color = tuple(max(0, min(255, c)) for c in shaded_color)

                # Aplicar un efecto de color basado en la densidad. Esto puede variar según el tipo de terreno.
                density_value = terrain.density_map[y, x] # Valor de densidad (0.0 a 1.0).
                density_color_effect = (0, 0, 0) # Por defecto no hay efecto de color por densidad.
                if terrain_type == TerrainType.FOREST:
                     # En bosques, añadir un tinte verde basado en la densidad (representa vegetación más densa).
                     density_tint = int(density_value * 150 * self.colors['variation']['density_factor'])
                     density_color_effect = (0, density_tint, 0)
                elif terrain_type == TerrainType.MOUNTAIN:
                     # En montañas, oscurecer basado en la densidad (representa rocas/terreno más accidentado).
                     darken_amount = int(density_value * 80 * self.colors['variation']['density_factor'])
                     density_color_effect = (-darken_amount, -darken_amount, -darken_amount)
                # Puedes añadir lógica similar para otros tipos de terreno (arena, agua, etc.) si deseas efectos específicos de densidad.


                # Calcular el color final del terreno combinando el sombreado de altura y el efecto de densidad.
                final_terrain_color = (
                     max(0, min(255, shaded_color[0] + density_color_effect[0])),
                     max(0, min(255, shaded_color[1] + density_color_effect[1])),
                     max(0, min(255, shaded_color[2] + density_color_effect[2]))
                )
                # Dibujar el rectángulo de la celda con el color final del terreno.
                pygame.draw.rect(self.screen, final_terrain_color, rect)


                # --- 2. Draw Conquest Status ---
                # Dibujar overlays para mostrar el estado de conquista y control inmediato.

                cell_conquest_map = conquest_map[y, x] # Estado de conquista oficial de la celda (0, 1, 2).
                cell_conquest_progress = conquest_progress[y, x] # Progreso de conquista (0.0 a 1.0).
                cell_control_points = control_points[y, x] # Quién controla inmediatamente (por presencia de unidades) (0, 1, 2).


                # Layer 1: Dibujar el color base del territorio oficialmente conquistado (semi-sólido).
                # Esta capa representa las zonas de control estables.
                if cell_conquest_map > 0: # Si la celda está conquistada por algún equipo.
                    # Obtener el color del territorio para el equipo conquistador.
                    territory_color = self.colors['territory'][cell_conquest_map]
                    # Crear una superficie semi-transparente para el color del territorio.
                    territory_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA) # Usar SRCALPHA para transparencia.
                    opacity = 180 # Opacidad alta para el territorio oficialmente controlado (valor entre 0 y 255).
                    territory_surface.fill((territory_color.r, territory_color.g, territory_color.b, opacity))
                    # Dibujar la superficie semi-transparente sobre la celda.
                    self.screen.blit(territory_surface, rect)


                # Layer 2: Dibujar un indicador visual para áreas bajo influencia activa/contienda (donde hay unidades).
                # Esta capa resalta las áreas de 3x3 alrededor de las unidades, mostrando dónde se está ejerciendo control inmediato.
                if cell_control_points > 0: # Si algún equipo tiene control inmediato sobre esta celda.
                    # Obtener el color del equipo que tiene el control inmediato.
                    indicator_color_rgb = self.colors['units'][cell_control_points]

                    # Crear una superficie semi-transparente para el indicador.
                    indicator_surface = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                    # La opacidad se define en 'contested_indicator' para facilitar el ajuste.
                    opacity = self.colors['contested_indicator']['overlay_alpha'] # Opacidad fija para el indicador de influencia.
                    indicator_surface.fill((indicator_color_rgb.r, indicator_color_rgb.g, indicator_color_rgb.b, opacity))
                    # Dibujar la superficie del indicador sobre la celda.
                    self.screen.blit(indicator_surface, rect)

                    # Opcional: Dibujar un borde alrededor de las celdas que están bajo influencia activa para hacerlas más visibles.
                    border_color = self.colors['contested_indicator']['border_color'] # Color del borde (ej. Amarillo).
                    # Dibujar un rectángulo (borde) sobre la celda. El último parámetro es el ancho del borde.
                    pygame.draw.rect(self.screen, border_color, rect, 1) # Dibuja un borde de 1 píxel.


    def draw_units(self, battle: Battle) -> None:
        """Draw all units in the battle."""
        # Las unidades se dibujan DESPUÉS del terreno y los overlays de conquista
        # para asegurar que siempre sean visibles en la parte superior.

        # Iterar sobre los equipos y sus unidades en la batalla.
        for team_id, team_units in battle.units.items():
            # Obtener el color para el equipo actual. Si el team_id no tiene color definido, saltar este equipo.
            if team_id not in self.colors['units']:
                 continue # Saltar si el team_id no tiene un color de unidad configurado.

            color = self.colors['units'][team_id] # Color de las unidades de este equipo.

            # Iterar sobre cada unidad del equipo.
            for unit in team_units:
                # Solo dibujar unidades que estén vivas.
                if unit.health > 0:
                    # Convertir la posición flotante de la unidad a coordenadas de píxeles para dibujar.
                    x = int(unit.position[0] * self.cell_size)
                    y = int(unit.position[1] * self.cell_size)

                    # Dibujar el cuerpo de la unidad (un círculo).
                    # Se dibuja un círculo con el color del equipo en la posición de la unidad.
                    pygame.draw.circle(self.screen, color, (x, y), self.cell_size // 2) # Radio es la mitad del tamaño de la celda.

                    # Dibujar la barra de vida de la unidad sobre su cuerpo.
                    max_health = 5 # Asumimos que la salud máxima inicial es 5 (según tu config/clase Unit).
                    # Calcular el ancho de la barra de vida en píxeles, proporcional a la salud actual.
                    # Se asegura que el ancho no sea negativo o mayor que el tamaño de la celda.
                    health_width = max(0, min(self.cell_size, (self.cell_size * unit.health) // max_health))
                    health_height = 2 # Altura fija de la barra de vida en píxeles.
                    # Calcular la posición del rectángulo de la barra de vida.
                    # Se coloca justo encima del círculo de la unidad.
                    health_rect = pygame.Rect(
                        x - self.cell_size//2, # Empezar a la izquierda del centro del círculo.
                        y - self.cell_size//2 - 4, # Empezar un poco más arriba que el borde superior del círculo.
                        health_width, # El ancho calculado basado en la salud.
                        health_height # La altura fija.
                    )
                    # Determinar el color de la barra de vida según el porcentaje de salud restante.
                    if unit.health > max_health * 0.6: # Más del 60% de salud.
                         health_color = (0, 255, 0) # Verde.
                    elif unit.health > max_health * 0.2: # Más del 20% y hasta 60% de salud.
                         health_color = (255, 165, 0) # Naranja.
                    else: # 20% de salud o menos.
                         health_color = (255, 0, 0) # Rojo.

                    # Dibujar el rectángulo de la barra de vida.
                    pygame.draw.rect(self.screen, health_color, health_rect)


    def draw_stats_panel(self, battle: Battle) -> None:
        """Draw detailed statistics panel on the right side of the screen."""
        # Obtener las estadísticas actuales de la batalla.
        stats = battle.get_battle_stats()

        # Dibujar el rectángulo gris oscuro para el fondo del panel de estadísticas.
        # Se coloca a la derecha de la cuadrícula del terreno.
        panel_rect = pygame.Rect(self.width, 0, 200, self.height) # Ancho 200px, alto como la cuadrícula.
        pygame.draw.rect(self.screen, (50, 50, 50), panel_rect) # Color gris oscuro.

        # Posición inicial para dibujar el texto en el panel.
        y_pos = 10 # Margen superior inicial.
        padding = 20 # Espacio vertical entre líneas de texto.

        # Dibujar el número del paso de simulación actual.
        self._draw_text(f"Step: {stats.get('step', 0)}", (self.width + 10, y_pos), color=(255, 255, 255)) # Blanco para el texto.
        y_pos += padding # Mover la posición Y para la siguiente línea.

        # Dibujar una línea separadora.
        pygame.draw.line(self.screen, (100, 100, 100), # Color gris medio para la línea.
                        (self.width + 10, y_pos), # Punto inicial (X, Y).
                        (self.width + 190, y_pos)) # Punto final (X, Y).
        y_pos += padding # Mover la posición Y después de la línea.

        # Dibujar estadísticas por equipo.
        # Iterar sobre los IDs de equipo esperados (1 y 2) para asegurar que se muestran las estadísticas para ambos.
        for team_id in [1, 2]: # Asumiendo IDs de equipo 1 y 2.
            # Obtener el color del equipo para el texto de encabezado. Usar color por defecto si no está definido.
            team_color = self.colors['units'].get(team_id, (200, 200, 200))
            # Asegurarse de que el color sea una tupla RGB si Pygame.Color lo devuelve.
            if isinstance(team_color, pygame.Color):
                 team_color = (team_color.r, team_color.g, team_color.b)


            # Dibujar el encabezado del equipo (ej. "Team 1").
            self._draw_text(f"Team {team_id}", (self.width + 10, y_pos), color=team_color)
            y_pos += padding # Mover Y.

            # Unidades restantes vivas.
            units_remaining = stats.get('units_remaining', {}).get(team_id, 0) # Usar .get() anidados para seguridad.
            self._draw_text(f"Units: {units_remaining}", (self.width + 20, y_pos)) # Indentar un poco a la derecha.
            y_pos += padding # Mover Y.

            # Porcentaje de territorio controlado.
            territory = stats.get('territory_control', {}).get(team_id, 0.0) # Usar .get() anidados para seguridad.
            self._draw_text(f"Territory: {territory:.1f}%", (self.width + 20, y_pos)) # Formato con 1 decimal.
            y_pos += padding # Mover Y.

            # Unidades enemigas eliminadas (Kills).
            kills = stats.get('total_kills', {}).get(team_id, 0) # Usar .get() anidados para seguridad.
            self._draw_text(f"Kills: {kills}", (self.width + 20, y_pos)) # Indentar a la derecha.
            y_pos += padding # Mover Y.

            # Unidades perdidas (bajas propias).
            losses = stats.get('casualties', {}).get(team_id, 0) # Usar .get() anidados para seguridad.
            self._draw_text(f"Losses: {losses}", (self.width + 20, y_pos)) # Indentar a la derecha.
            y_pos += padding * 1.5 # Espacio extra entre equipos.


    def _draw_text(self, text: str, position: Tuple[int, int], color=(200, 200, 200)):
        """Helper method to draw text on the screen."""
        # Asegurarse de que el sistema de fuentes de Pygame está inicializado.
        if not pygame.font.get_init():
             # Si por alguna razón no lo está, inicializarlo (debería ser inicializado en __init__).
             pygame.font.init()
             # Puede ser necesario recrear el objeto fuente si el sistema de fuentes se reinicializó.
             self.font = pygame.font.SysFont(None, 24)

        # Renderizar el texto en una superficie.
        text_surface = self.font.render(text, True, color)
        # Dibujar la superficie del texto en la pantalla principal en la posición especificada.
        self.screen.blit(text_surface, position)


    def update(self, battle: Battle) -> bool:
        """
        Updates the Pygame display by drawing the current state of the battle.
        Processes Pygame events to detect window closure.
        Returns True if the simulation should continue, False if the window was closed (QUIT event).
        """
        # Procesar todos los eventos de Pygame en la cola. Esto es necesario para que la ventana de Pygame
        # responda a interacciones del usuario (como cerrarla) y para mantenerla activa.
        for event in pygame.event.get():
            # Si el tipo de evento es Pygame.QUIT (el usuario cerró la ventana).
            if event.type == pygame.QUIT:
                # Si la ventana fue cerrada, indicar al main loop que la simulación debe detenerse.
                return False # Retorna False para señalar que se detectó el cierre.

        # Si no se detectó evento de cierre, proceder a dibujar el estado actual.
        # Asegurarse de que el objeto de pantalla (self.screen) es válido antes de intentar dibujar en él.
        # Podría ser None si la inicialización de la pantalla falló en __init__ o reset_display.
        if self.screen is None:
             print("Warning: Pygame screen is not initialized, cannot update visualizer.")
             # No hubo evento de cierre, pero no se puede dibujar. Retorna True para intentar continuar,
             # pero el error de inicialización podría haber sido fatal de todos modos.
             return True


        # Limpiar la pantalla antes de dibujar los elementos del nuevo paso.
        self.screen.fill((0, 0, 0)) # Rellenar con negro.

        # Dibujar los diferentes componentes de la simulación en capas.
        self.draw_terrain(battle.terrain) # Dibuja el terreno, incluyendo el estado de conquista.
        self.draw_units(battle) # Dibuja las unidades sobre el terreno y la conquista.
        self.draw_stats_panel(battle) # Dibuja el panel de estadísticas.

        # Actualizar toda la pantalla de Pygame para mostrar lo que se ha dibujado.
        pygame.display.flip()

        # Indicar que no se detectó evento de cierre y que la actualización se completó (o se intentó).
        return True # Retorna True para indicar que la simulación puede continuar.


    def quit_pygame(self):
        """Quit pygame systems."""
        # Esta función es la única responsable de llamar a pygame.quit().
        # Debe ser llamada UNA VEZ al final de la vida de la aplicación (desde end_simulation en main.py).
        # Verifica si Pygame está inicializado antes de intentar cerrarlo.
        if pygame.get_init():
             pygame.quit() # Cierra todos los módulos de Pygame.
             self.screen = None # Opcional: Limpiar la referencia a la pantalla después de cerrarla.


    def reset_display(self, width: int, height: int, cell_size: int):
        """
        Reset or re-initialize the display window (resize and set caption).
        Assumes pygame.init() is already called.
        """
        # Esta función se llama en init_simulation (cuando se resetea la simulación)
        # para asegurar que la ventana de Pygame tenga el tamaño correcto según el nuevo terreno.

        self.grid_width = width
        self.grid_height = height
        self.cell_size = cell_size
        self.width = self.grid_width * self.cell_size
        self.height = self.grid_height * self.cell_size

        try:
            # Re-establecer el modo de visualización para cambiar el tamaño de la ventana.
            # Esto requiere que Pygame esté inicializado.
            self.screen = pygame.display.set_mode((self.width + 200, self.height))
            # Actualizar el título de la ventana.
            pygame.display.set_caption("War Simulator")
            # Si la fuente necesita ser reinicializada después de cambiar el modo de display, hazlo aquí.
            # pygame.font.init()
            # self.font = pygame.font.SysFont(None, 24)

        except pygame.error as e:
            # Si ocurre un error al re-establecer la pantalla (ej. Pygame fue quitado inesperadamente),
            # imprime el error pero permite que la aplicación principal decida si salir.
            print(f"Error setting display mode during reset: {e}")
            self.screen = None # Marcar la pantalla como no válida si falló.
            pass # No forzar la salida aquí.