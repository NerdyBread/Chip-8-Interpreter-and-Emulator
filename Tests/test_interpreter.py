import sys
import os
import pytest

source_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, source_path)

from emulator import Emulator

class TestInterpreterHelpers:
    @pytest.fixture
    def test_opcode(self):
        return 0x1234
    
    @pytest.fixture
    def interpreter(self):
        return Emulator().interpreter
        
    def test_get_addr(self, test_opcode, interpreter):
        assert interpreter.get_addr(test_opcode) == 0x234
        
    def test_get_x(self, test_opcode, interpreter):
        assert interpreter.get_x(test_opcode) == 0x2

    def test_get_y(self, test_opcode, interpreter):
        assert interpreter.get_y(test_opcode) == 0x3

    def test_get_kk(self, test_opcode, interpreter):
        assert interpreter.get_kk(test_opcode) == 0x34
    
class TestRegisterMath:
    """Tests the 0x8xy_ instructions"""
    @pytest.fixture
    def x(self) -> int:
        return 0x0
    
    @pytest.fixture
    def y(self) -> int:
        return 0xE
    
    @pytest.fixture
    def x_val(self) -> int:
        """Default value for x"""
        return 0b11000101
    
    @pytest.fixture
    def y_val(self) -> int:
        """Default value for y"""
        return 0b10011001
    
    @pytest.fixture
    def interpreter(self, x, y, x_val, y_val):
        """Creates a new interpreter object with test values preloaded"""
        vm = Emulator()
        vm.interpreter.v[x] = x_val
        vm.interpreter.v[y] = y_val
        
        return vm.interpreter
    
    def test_set_equal(self, x, y, interpreter):
        """8xy0: x = y"""
        initial_value = 0x1234
        interpreter.v[y] = initial_value
        interpreter.run_instruction(0x80E0)
        assert interpreter.v[y] == interpreter.v[x] == initial_value
    
    def test_or(self, x, y, x_val, y_val, interpreter):    
        """8xy1: x = x OR y"""
        interpreter.run_instruction(0x80E1)
        assert interpreter.v[x] == x_val | y_val
        assert interpreter.v[y] == y_val
        
    def test_and(self, x, y, x_val, y_val, interpreter):    
        """8xy2: x = x AND y"""
        interpreter.run_instruction(0x80E2)
        assert interpreter.v[x] == x_val & y_val
        assert interpreter.v[y] == y_val
        
    def test_xor(self, x, y, x_val, y_val, interpreter):    
        """8xy3: x = x XOR y"""
        interpreter.run_instruction(0x80E3)
        assert interpreter.v[x] == x_val ^ y_val
        assert interpreter.v[y] == y_val
        
    def test_add_no_overflow(self, x, y, interpreter):
        """8xy4: x = x + y, VF = carry bit"""
        small_x_val = 0b00001111
        small_y_val = 0b00110000
        interpreter.v[x] = small_x_val
        interpreter.v[y] = small_y_val
        interpreter.run_instruction(0x80E4)
        assert interpreter.v[x] == small_x_val + small_y_val
        assert interpreter.v[y] == small_y_val
        assert interpreter.v[0xF] == 0
        
    def test_add_overflow(self, x, y, x_val, y_val, interpreter):
        interpreter.run_instruction(0x80E4)
        result = (x_val + y_val) & 0xFF # Only lowest 8 bits are saved
        assert interpreter.v[x] == result
        assert interpreter.v[y] == y_val
        assert interpreter.v[0xF] == 1
        
    def test_subtraction_no_underflow(self, x, y, interpreter):
        small_x_val = 0b00110000
        small_y_val = 0b00111111
        interpreter.v[x] = small_x_val
        interpreter.v[y] = small_y_val
        interpreter.run_instruction(0x80E5)
        assert interpreter.v[x] == (small_x_val - small_y_val) % 256
        assert interpreter.v[0xF] == 0
    
    def test_subtraction_underflow(self, x, y, interpreter):
        small_x_val = 0b00111111
        small_y_val = 0b00110000
        interpreter.v[x] = small_x_val
        interpreter.v[y] = small_y_val
        interpreter.run_instruction(0x80E5)
        assert interpreter.v[x] == (small_x_val - small_y_val) % 256
        assert interpreter.v[0xF] == 1
        
    def test_right_shift_carry(self, x, interpreter):
        interpreter.v[x] &= 0b11111110
        original = interpreter.v[x]
        interpreter.run_instruction(0x8016)
        # y isn't used here unless we get into quirks
        assert interpreter.v[x] == (original // 2) == (original >> 1)
        assert interpreter.v[0xF] == 0
        
    def test_right_shift_carry_overflow(self, x, interpreter):
        original = interpreter.v[x]
        interpreter.run_instruction(0x8016)
        # y isn't used here unless we get into quirks
        assert interpreter.v[x] == (original // 2) == (original >> 1)
        assert interpreter.v[0xF] == 1
    
    def test_flipped_subtraction_no_underflow(self, x, y, interpreter):
        small_x_val = 0b00111111
        small_y_val = 0b00110000
        interpreter.v[x] = small_x_val
        interpreter.v[y] = small_y_val
        interpreter.run_instruction(0x80E7)
        assert interpreter.v[x] == (small_y_val - small_x_val) % 256
        assert interpreter.v[0xF] == 0
    
    def test_flipped_subtraction_underflow(self, x, y, interpreter):
        small_x_val = 0b00110000
        small_y_val = 0b00111111
        interpreter.v[x] = small_x_val
        interpreter.v[y] = small_y_val
        interpreter.run_instruction(0x80E7)
        assert interpreter.v[x] == (small_y_val - small_x_val) % 256
        assert interpreter.v[0xF] == 1
    
    def test_left_shift(self, x, interpreter):
        original = 0b00001111
        interpreter.v[x] = original
        interpreter.run_instruction(0x801E)
        # y isn't used here unless we get into quirks
        assert interpreter.v[x] == original << 1
        assert interpreter.v[0xF] == 0
        
    def test_left_shift_overflow(self, x, interpreter):
        original = interpreter.v[x]
        interpreter.run_instruction(0x801E)
        # y isn't used here unless we get into quirks
        assert interpreter.v[x] == ((original << 1) & 255)
        assert interpreter.v[0xF] == 1
        
def test_set_pc():
    interpreter = Emulator().interpreter
    interpreter.run_instruction(0x1400)
    assert interpreter.pc == 0x400

def test_stack_operations():
    interpreter = Emulator().interpreter
    start_addr = 0x200
    interpreter.pc = start_addr
    assert len(interpreter.stack) == 0
    interpreter.run_instruction(0x2300)
    assert interpreter.stack[0] == start_addr
    interpreter.run_instruction(0x00EE)