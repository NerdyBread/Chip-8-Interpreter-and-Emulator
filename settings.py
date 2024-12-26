class Settings:
    def __init__(self):
        # Display
        self.screen_off = (0, 0, 0)
        self.screen_on = (255, 255, 255)
        self.screen_width = 64
        self.screen_height = 32
        self.pixels_per_bit = 15
        
        # Emulator config
        self.instructions_per_second = 660
        self.refresh_rate = 60 # Hz