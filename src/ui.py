import pygame
from typing import Callable, Tuple

class UIElement:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

    def draw(self, screen):
        pass

class Button(UIElement):
    def __init__(self, x, y, w, h, text, callback: Callable, color=(50, 50, 50), hover_color=(70, 70, 70)):
        super().__init__(x, y, w, h)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.font = pygame.font.SysFont("Arial", 14)

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hovered:
                self.callback()
                return True
        return False

    def draw(self, screen):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=4)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 1, border_radius=4) # Border
        
        text_surf = self.font.render(self.text, True, (220, 220, 220))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

class Slider(UIElement):
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label, callback: Callable):
        super().__init__(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.callback = callback
        self.dragging = False
        self.handle_w = 10
        self.font = pygame.font.SysFont("Arial", 12)

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_val(event.pos[0])

    def update_val(self, mouse_x):
        ratio = (mouse_x - self.rect.x) / self.rect.w
        ratio = max(0, min(1, ratio))
        self.val = self.min_val + (self.max_val - self.min_val) * ratio
        self.callback(self.val)

    def draw(self, screen):
        # Label
        label_surf = self.font.render(f"{self.label}: {self.val:.2f}", True, (200, 200, 200))
        screen.blit(label_surf, (self.rect.x, self.rect.y - 15))

        # Bar
        pygame.draw.rect(screen, (40, 40, 40), self.rect, border_radius=2)
        
        # Fill
        ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.w * ratio, self.rect.h)
        pygame.draw.rect(screen, (60, 100, 150), fill_rect, border_radius=2)

        # Handle
        handle_x = self.rect.x + (self.rect.w * ratio) - (self.handle_w / 2)
        handle_rect = pygame.Rect(handle_x, self.rect.y - 2, self.handle_w, self.rect.h + 4)
        pygame.draw.rect(screen, (200, 200, 200), handle_rect, border_radius=2)
