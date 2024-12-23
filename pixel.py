import pygame

class Pixel:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x*size, y*size, size, size)
        
    def get_rect(self):
        return self.rect