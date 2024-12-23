"""
Emulator for the RCA COSMAC VIP computer

~~~~~~~~~~~~~~~~~~~~~
System Specifications
~~~~~~~~~~~~~~~~~~~~~

Memory:
    4096 bytes
    - The original machine had 2048 bytes of RAM but could be expanded to 4096
    - The first 512 bytes aren't used as this is where the chip8 interpreter was stored

Registers:
    V0-VF - 16 8 bit general purpose registers
    I - Extra 16 bit register (usually for sprites)
    Sound - Counts down to 0 at 60Hz (more info below)
    Delay - Counts down to 0 at 60Hz like the sound register

    "Pseudoregisters" (Not accessed by the programs):
    Stack - array of sixteen two byte values
    Stack pointer - points to current topmost level of the stack
    Program counter - 16 bits used to store the address of whatever instruction is currently being executed
    
Hexadecimal Keypad:
    Originally:
        123C
        456D
        789E
        A0BF
    - Modern interpreters map this to keys that make more sense
    - This one uses:
        1234
        qwer
        asdf
        zxcv
    
Outputs:
    Screen:
    - The original Chip 8 language mapped to a 64x32 pixel screen
    - The coordinates go from (0, 0) in the top left to (63, 31) in the bottom right
    Sound:
    - A buzzer plays whenever the above mentioned sound timer is not 0

"""
from time import sleep, time # For testing ideas

import pygame
from pygame import mixer

from chip8 import Interpreter
from pixel import Pixel
from settings import Settings

class VM:
    def __init__(self):
        self.settings = Settings()
        self.memory = [0x00] * 0x1000 # Don't touch 0x0 - 0x1FF
        self.v = [0x00] * 0x10
        self.I = 0x0000
        self.delay_timer = 0x0
        self.sound_timer = 0x0
        # 750 instructions per second
        # .750 instructions per millisecond
        # 1/750 = seconds per instruction
        # *1000 = milliseconds per instruction
        self.timer_pause = int((1 / self.settings.timer_frequency) * 1000) # In millisecods
        # Setup timers to go down by one every 1/60 seconds
        pygame.init()
        self.TIMERS_DOWN = pygame.USEREVENT + 1
        pygame.time.set_timer(self.TIMERS_DOWN, self.timer_pause)
        
        # Setup instructions to run the number of times per second
        # specified in settings.py
        between_instructions = 1 / self.settings.instructions_per_second
        milliseconds_per = int(between_instructions * 1000)
        self.RUN_INSTRUCTION = pygame.USEREVENT + 2
        pygame.time.set_timer(self.RUN_INSTRUCTION, milliseconds_per)
        
        self.TRY_PLAY_SOUND = pygame.USEREVENT + 3
        pygame.time.set_timer(self.TRY_PLAY_SOUND, 40)

        
        # Set up key callbacks
        self.KEY_MAP = {
            pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
            pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
            pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
            pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF
            }
        
        self.key_buffer = [0] * 0x10 # ex - key_buffer[5] corresponds to w key
    
        self.setup_display()
        self.interpreter = Interpreter(self)
        
        sound_file = "sound.wav"
        mixer.init()
        mixer.music.load(sound_file)
        mixer.music.set_volume(0.8)
        
    def setup_display(self):
        """Configure the pygame display, setup the 2D array of pixels"""
        self.screen_width = self.settings.screen_width
        self.screen_height = self.settings.screen_height
        self.pixels_per_bit = self.settings.pixels_per_bit
        
        self.screen = pygame.display.set_mode((self.screen_width*self.pixels_per_bit,
                                               self.screen_height*self.pixels_per_bit))
        self.screen.fill(self.settings.screen_off)
        self.screen_rect = self.screen.get_rect()
        
        # Subroutine generates an array of blank pixels
        self.pixels = [[Pixel(x, y, self.pixels_per_bit) 
                        for x in range(self.screen_width)]
                       for y in range(self.screen_height)]
        
        """
        For readability it essentially does this
        for y in range(len(self.pixels)):
            for x in range(len(self.pixels[0])):
                self.pixels[y][x] = Pixel(x, y, self.pixels_per_bit)
        """
                
        self.on_color = self.settings.screen_on
        self.off_color = self.settings.screen_off
        
    def get_rom_file(self):
        """Prompts user to load in a .ch8 ROM file"""
        return input("Enter Chip8 ROM file name: ")
        
    def load_rom(self, fn):
        file = open(fn, 'rb').read()
        for i in range(len(file)):
            self.memory[0x200+i] = file[i]
    
    def display_handler(self):
        for y, row in enumerate(self.pixels):
            for x, pixel in enumerate(row):
                # Get the pygame surface for the pixel
                rect = pixel.get_rect()
                # Read in screen buffer
                on = self.interpreter.screen_buffer[y][x] 
                if on:
                    color = self.on_color
                else:
                    color = self.off_color
                pygame.draw.rect(self.screen, color, rect)
        pygame.display.flip()
        
    def timers_down(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
    
    def run(self):
        # Ask to load in a program
        file_name = self.get_rom_file()
        self.load_rom(file_name)
        running = True
        while running:
            # Pygame event handler
            for event in pygame.event.get():
                if event == pygame.QUIT:
                    running = False
                # Handle timers
                if event.type == self.TIMERS_DOWN:
                    self.timers_down()
                # Handle cpu cycle
                if event.type == self.RUN_INSTRUCTION:
                    # next = hex(self.interpreter.get_next_instruction())
                    # If I ever want to make a debugger
                    self.interpreter.cycle()
                # Handle display
                if self.interpreter.get_draw_flag():
                    self.display_handler()
                    self.interpreter.set_draw_flag(False)
                    
                # Handle keyboard
                if event.type == pygame.KEYDOWN:
                    if event.key in self.KEY_MAP:
                        idx = self.KEY_MAP[event.key]
                        self.key_buffer[idx] = 1
                            
                if event.type == pygame.KEYUP:
                    if event.key in self.KEY_MAP:
                        idx = self.KEY_MAP[event.key]
                        self.key_buffer[idx] = 0
                            
                if event.type == self.TRY_PLAY_SOUND:
                    self.play_sound()
                        
    def get_delay_timer(self):
        return self.delay_timer
    
    def set_delay_timer(self, new):
        self.delay_timer = new
    
    def get_sound_timer(self):
        return self.sound_timer
    
    def set_sound_timer(self, new):
        self.sound_timer = new
        
    def play_sound(self):
        if self.get_sound_timer():
            mixer.music.play()
            
if __name__ == "__main__":       
    machine = VM()
    machine.run()