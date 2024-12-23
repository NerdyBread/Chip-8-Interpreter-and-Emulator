import os
import sys

import pygame

source_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, source_path)

from emulator import VM

class TestEmulator:
    def single_pixel_test(self, x, y):
        """Not a pytest test"""
        self.machine = VM()
        pixel = self.machine.pixels[y][x]
        pixel.set_state(1)
        pygame.draw.rect(self.machine.screen, self.machine.on_color, pixel.get_rect())
        print(f"x: {x}")
        print(f"y: {y}")
        while True:
            pygame.display.flip()