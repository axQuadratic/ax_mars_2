# This file stores classes and global variables for easy access
# It also manages the inner workings of the setup and options menus

import customtkinter as ctk
from enum import Enum
from random import randint

class tile_colors(Enum):
    blue = (0, 200, 200)
    red = (200, 0, 0)
    green = (0, 200, 0)
    yellow = (200, 200, 0)
    white = (255, 255, 255)
    black = (10, 10, 10)
    highlight = (25, 66, 113)

# The below lists are compiled from ICWS 94: https://corewar.co.uk/standards/icws94.htm
addressing_modes = [
    "#", "$", "*", "@", "{", "<", "}", ">"
]

modifiers = [
    "A", "B", "AB", "BA", "F", "X", "I"
]

opcodes = [
    "DAT", "MOV", "ADD", "SUB", "MUL", "DIV", "MOD", "JMP", "JMZ", "JMN", "DJN", "SPL", "CMP", "SEQ", "SNE", "SLT", "LDP", "STP", "NOP"
]

class Instruction:
    def __init__(self, label : str, opcode : str, modifier : str, a_mode_1 : str, address_1, a_mode_2 : str, address_2):
        self.label = label
        self.opcode = opcode
        self.modifier = modifier
        self.a_mode_1 = a_mode_1
        self.address_1 = address_1
        self.a_mode_2 = a_mode_2
        self.address_2 = address_2

class Warrior:
    def __init__(self, name : str, id : int, color : str, raw_data : list, load_file : list):
        self.name = name
        self.id = id
        self.color = color
        self.raw_data = raw_data
        self.load_file = load_file

class Tile:
    def __init__(self, warrior : int, color : str, instruction : Instruction, highlighted : bool):
        self.warrior = warrior
        self.color = color
        self.instruction = instruction
        self.highlighted = highlighted

# This is declared here, so it can be accessed by other files
root = ctk.CTk()

play_speed = 1
field_size = 8000
max_cycle_count = 80000
max_program_length = 100

warriors = [1, 2, 3, 4] # Temporary values

state_data = [Tile(1, "black", "DAT.F #0, #0", False) for i in range(20000)]
prev_state_data = []

state_image = None
resized_state_image = None

speed_levels = [1, 2, 3, 4, 5, 10, 25, 50, 75, 100]

render_queue = []

# Setup menu

def apply_setup(window, label, core_size, max_cycles, max_length, random_core):
    global field_size, max_cycle_count, max_program_length

    # Error checking
    try:
        if random_core == 1:
            core_size = randint(max_length * len(warriors), 20000)

        core_size = int(core_size)
        max_cycles = int(max_cycles)
        max_length = int(max_length)

        if max_cycles <= 0 or max_length <= 0:
            raise Exception
    except:
        label.configure(text="One or more parameters has an invalid value")
        return
    
    if core_size < max_length * len(warriors):
        label.configure(text="Core size cannot be smaller than max. warrior length * warrior count")
        return
    
    field_size = core_size
    max_cycle_count = max_cycles
    max_program_length = max_length
    
    window.destroy()
    render_queue.append(state_data) # The core viewer, if it is open, needs to be updated

# Options menu

def toggle_dark_mode():
    if ctk.get_appearance_mode() == "Light":
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")