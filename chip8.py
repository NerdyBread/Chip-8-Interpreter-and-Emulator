"""Interpreter for all opcodes of the original Chip8 language"""

from random import randint

from fonts import Fonts

class Interpreter:
    def __init__(self, machine):
        """These registers are technically in the machine memory but
        aren't accessed by the program (i.e. they are only used by the
        interpreter internally)"""
        self.stack = []
        self.pc = 0x0200
        # Make references now so we don't have to access through the VM later
        self.machine = machine
        self.memory = machine.memory
        self.v = machine.v
        self.I = machine.I
        self.key_buffer = machine.key_buffer
        self.stored_key = None # For Fx0A
        self.empty_screen_buffer()
        # Flags to make execution a little smoother
        self.waiting_for_press = False
        
        # Load in the chip8 hexadecimal sprite fontset
        fonts = Fonts()
        self.fonts = fonts.font_arr
        for i in range(80):
            self.memory[i] = self.fonts[i]
        
        # Constants for graphics wraparound  
        self.ROW_LEN = len(self.screen_buffer[0])
        self.COLUMN_LEN = len(self.screen_buffer)
        
        
    def cycle(self):
        opcode = self.get_next_instruction()
        self.pc += 2
        self.run_instruction(opcode)
        
    def get_next_instruction(self):
        """
        Fetch the next opcode by getting the byte at the program counter
        and the byte after
        """
        # Each instruction is two bytes so PC generally goes up by 2
        # i.e. The start of each instruction should be at an even number
        first_byte = self.memory[self.pc]
        second_byte = self.memory[self.pc+1]
        return first_byte << 8 | second_byte # Add 8 zeros and OR with second byte to combine
    
    def empty_screen_buffer(self):
        w = self.machine.screen_width
        h = self.machine.screen_height
        self.screen_buffer = [[0] * w for i in range(h)]
    
    def run_instruction(self, opcode):
        # Get all the different opcode segments we might need
        addr = self.get_addr(opcode) # Lowest 12 bits
        x = self.get_x(opcode) # Low nibble of the higher byte
        y = self.get_y(opcode) # High nibble of the lower byte
        byte = self.get_kk(opcode) # Low byte of the instruction
        if not self.waiting_for_press:
            self.key_cache = self.key_buffer.copy()
        # I love the term nibble
        
        match (opcode & 0xF000): # Check highest 4 bits
            case 0x0000: # 0x0???
                match (opcode & 0x0FFF):
                    case (0x00E0): # 0x00E0
                        # Clear the display
                        self.empty_screen_buffer()
                        
                    case (0x00EE): # 0x00EE
                        # Return from current subroutine
                        self.pc = self.stack.pop()

            case 0x1000: # 0x1nnn
                # Set program counter to address nnn
                self.pc = addr
            
            case 0x2000: # 0x2nnn
                # Call subroutine at addr nnn
                self.stack.append(self.pc)
                # print([hex(val) for val in self.stack])
                if len(self.stack) > 16:
                    raise MemoryError("Stack height cannot exceed 16") # This theoretically shouldn't happen
                # Most programs don't even use 8 but this is more to be accurate
                self.pc = addr
                        
            case 0x3000: # 0x3xkk
                # Skip next instruction if Vx == kk
                if self.v[x] == byte:
                    self.pc += 2
            
            case 0x4000: # 0x4xkk
                # Skip next instruction if Vx != kk
                if self.v[x] != byte:
                    self.pc += 2
            
            case 0x5000: # 0x5xy0
                # Skip next instruction if Vx == Vy
                if self.v[x] == self.v[y]:
                    self.pc += 2
            
            case 0x6000: # 0x6xkk
                # Set Vx to kk
                self.v[x] = byte
               
            case 0x7000: # 0x7xkk
                """Add value kk to register Vx, there is wraparound when
                result is greater than 255, i.e. lowest 8 bits are kept"""
                self.v[x] = (self.v[x] + byte) % 256
            
            case 0x8000: # 0x8xy?
                # Some operation with the variables
                match (opcode & 0x000F):
                    case 0x0000: # 0x8xy0
                        # Set Vx = Vy
                        self.v[x] = self.v[y]
                        
                    case 0x0001: # 0x8xy1
                        # Set Vx = Vx OR Vy
                        self.v[x] |= self.v[y]
                        self.v[0xF] = 0
                    
                    case 0x0002: # 0x8xy2
                        # Set Vx = Vx AND Vy
                        self.v[x] &= self.v[y]
                        self.v[0xF] = 0
                    
                    case 0x0003: # 0x8xy3
                         # Set Vx = Vx XOR Vy
                        self.v[x] ^= self.v[y]
                        self.v[0xF] = 0

                    case 0x0004: # 0x8xy4
                        # Add Vx and Vy, VF is carry
                        res = self.v[x] + self.v[y]
                        if res > 0xFF: # Max value
                            res %= 256
                            overflow = 1
                        else:
                            overflow = 0
                        self.v[x] = res
                        self.v[0xF] = overflow
                    
                    case 0x0005: # 0x8xy5
                        # Vx = Vx - Vy, VF = 1 if Vx > Vy
                        overflow = self.v[x] >= self.v[y]
                        self.v[x] = (self.v[x] - self.v[y]) % 256 # Chip8 is unsigned
                        self.v[0xF] = overflow
                    
                    case 0x0006: # 0x8xy6
                        # Vx = Vx >> 1, VF = least significant bit of Vx
                        lost_bit = self.v[x] & 1
                        self.v[x] = self.v[x] >> 1
                        self.v[0xF] = lost_bit
                    
                    case 0x0007: # 0x8xy7
                        # Vx = Vy - Vx, VF = 1 if Vy > Vx
                        overflow = self.v[y] >= self.v[x]
                        self.v[x] = (self.v[y] - self.v[x]) % 256 # Same as 8xy7
                        self.v[0xF] = overflow

                    case 0x000E: # 0x8xyE
                        # Shift Vx left 1 bit, VF is most significant bit of Vx
                        lost_bit = (self.v[x] & 0b10000000) >> 7
                        self.v[x] = (self.v[x] << 1) & 0xFF # Prevent overflow
                        self.v[0xF] = lost_bit
                    
            case 0x9000: # 9xy0
                # Skip next instruction if Vx != Vy
                if self.v[x] != self.v[y]:
                    self.pc += 2
                    
            
            case 0xA000: # Annn
                # Set I register to nnn
                self.I = addr
            
            case 0xB000: # Bnnn
                # Jump to addr nnn + V0
                self.pc = (addr + self.v[0])
            
            case 0xC000: # Cxkk
                # Vx = random byte & kk
                new_byte = randint(0, 255)
                self.v[x] = new_byte & byte

            case 0xD000: # Dxyn
                # Display n-byte sprite starting at addr in register I at (Vx, Vy), VF = collision
                bytes_in_sprite = opcode & 0x000F
                sprite = []
                for i in range(bytes_in_sprite):
                    sprite.append(self.memory[self.I + i])
                    
                x_coord = self.v[x]
                y_coord = self.v[y]
                self.v[0xF] = 0
                for i, row_index in enumerate(range(y_coord, y_coord+bytes_in_sprite)):
                    # So for each row we want to xor the byte at i with the 8 pixels in that row
                    comparison_byte = sprite[i]
                    # Scan across byte
                    for column in range(8):
                        # Each sprite is 8 bits wide
                        comparison_bit = (comparison_byte >> (7 - column)) & 1
                        x_idx = (column + x_coord) % self.ROW_LEN
                        row_index %= self.COLUMN_LEN
                        current_bit = self.screen_buffer[row_index][x_idx]
                        new_state = comparison_bit ^ current_bit
                        if current_bit == 1 and new_state == 0:
                            self.v[0xF] = 1
                        self.screen_buffer[row_index][x_idx] = new_state
            
            case 0xE000:
                match (opcode & 0x00FF):
                    case 0x009E: # Ex9E
                        # Skip next instruction if key at value Vx is pressed
                        key_idx = self.v[x] & 0xF
                        if self.key_buffer[key_idx]:
                            self.pc += 2
                    
                    case 0x00A1: # ExA1
                        # Skip next instruction if key at value Vx isn't pressed
                        key_idx = self.v[x] & 0xF
                        if not self.key_buffer[key_idx]:
                            self.pc += 2
            
            case 0xF000:
                match (opcode & 0x00FF):
                    case 0x0007: # Fx07
                        # Set V[x] to delay timer value
                        self.v[x] = self.machine.get_delay_timer()
                    
                    case 0x000A: # Fx0A
                        """
                        Pause execution to wait for new key press, then store key in Vx
                        1. Find keys that haven't been pressed
                        2. Wait for one of them to be pressed AND released
                        3. Store it in Vx
                        """
                        self.waiting_for_press = True
                        
                        for i in range(len(self.key_buffer)):
                            if self.key_buffer[i] != self.key_cache[i]:
                                self.stored_key = i
                                self.waiting_for_press = False
                                break
                        else:
                            self.stored_key = None
                            self.pc -= 2
                                
                        if self.stored_key != None:    
                            # We're waiting for a key release now
                            if self.key_buffer[self.stored_key] == 0:
                                self.stored_key == None    
                            else:
                                self.pc -= 2
                                
                        # Decrementing the pc makes this instruction loop                    
                    
                    case 0x0015: # Fx15
                        # Set delay timer to Vx
                        self.machine.set_delay_timer(self.v[x])
                    
                    case 0x0018: # Fx18
                        # Set sound timer to Vx
                        self.machine.set_sound_timer(self.v[x])
                    
                    case 0x001E: # Fx1E
                        # Add value of Vx to I
                        self.I += self.v[x]
                    
                    case 0x0029: # Fx29
                        # Set I to location of sprite for digit Vx
                        digit = self.v[x] & 0xF
                        self.I = digit * 5 # First byte of 5 in memory
                    
                    case 0x0033: # Fx33
                        # Store BCD representation of Vx in memory
                        # Hundreds digit in I, tens in I+1, ones in I + 2
                        decimal_vx = self.v[x]
                        ones = decimal_vx % 10
                        tens = (decimal_vx % 100) - ones
                        hundreds = decimal_vx - tens - ones
                        self.memory[self.I] = hundreds // 100
                        self.memory[self.I+1] = tens // 10
                        self.memory[self.I+2] = ones
                    
                    case 0x0055: # Fx55
                        # Store V0 through Vx in memory starting at I
                        register = 0
                        while register <= x:
                            self.memory[self.I + register] = self.v[register]
                            register += 1
                        self.I += x + 1 # Quirks
                    
                    case 0x0065: # Fx65
                        # Read memory starting at I into registers V0 through Vx
                        memory_addr = self.I
                        for num in range(x+1):
                            self.v[num] = self.memory[memory_addr + num]
                        self.I += x + 1 # Quirks
    
    def get_addr(self, opcode):
        """Return lowest 12 bits of the instruction"""
        return opcode & 0x0FFF
            
    def get_x(self, opcode):
        """Return the low 4 bits of the higher instruction"""
        return (opcode & 0x0F00) >> 8
    
    def get_y(self, opcode):
        """Return the high 4 bits of the lower instruction"""
        return (opcode & 0x00F0) >> 4
    
    def get_kk(self, opcode):
        """Return the lowest byte of the instruction"""
        return opcode & 0x00FF
        
class OpcodeNotFound(Exception):
    pass