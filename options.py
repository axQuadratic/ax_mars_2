# This file stores classes and global variables for easy access
# It also manages the inner workings of the setup and options menus

import customtkinter as ctk
from enum import Enum
from random import randint
from copy import deepcopy

class tile_colors(Enum):
    blue = (0, 200, 200)
    red = (200, 0, 0)
    green = (0, 200, 0)
    yellow = (200, 200, 0)
    orange = (255, 150, 0)
    purple = (110, 0, 255)
    pink = (255, 110, 230)
    gray = (200, 200, 200)
    white = (255, 255, 255)
    black = (10, 10, 10)
    highlight = (25, 66, 113)

# RGB to hex algorithm straight from Stackoverflow
def get_tile_hex_color(color : str):
    rgb = tile_colors[color].value
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])

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

warriors = []
warriors_temp = []

state_data = []
prev_state_data = []
cur_cycle = 0
process_queue = []

state_image = None
resized_state_image = None
render_queue = []

speed_levels = [1, 2, 3, 4, 5, 10, 25, 50, 75, 100]

def initialize_core():
    global state_data, prev_state_data, cur_cycle

    # Initialize a new core with all warriors and parameters
    state_data = [Tile(None, "black", Instruction(None, "DAT", "F", "#", 0, "#", 0), False) for i in range(field_size)]
    prev_state_data = []
    cur_cycle = 0

    # Place warriors at random positions
    for warrior in warriors:
        while True:
            warrior_pos = randint(0, len(state_data) - 1)

            # Check for the presence of other warriors in the covered range
            blocked = False
            for i in range(warrior_pos, warrior_pos + max_program_length):
                if state_data[i % field_size].warrior is not None:
                    blocked = True
            
            # Simple brute-force; reattempt placement if blocking warrior is found
            if not blocked: break

        # Once placement is found, place warrior
        i = warrior_pos
        for line in warrior.load_file:
            state_data[i % field_size] = Tile(warrior.id, warrior.color, line, False)
            i += 1

def parse_instruction_to_text(instruction : Instruction):
    return f"{instruction.opcode}.{instruction.modifier} {instruction.a_mode_1}{instruction.address_1}, {instruction.a_mode_2}{instruction.address_2}"

# Setup menu

def apply_setup(window, label, state_button, core_size, max_cycles, max_length, random_core):
    global field_size, max_cycle_count, max_program_length, warriors

    # Error checking
    try:
        if random_core == 1:
            core_size = randint(max_length * len(warriors), 20000)

        core_size = int(core_size)
        max_cycles = int(max_cycles)
        max_length = int(max_length)

        if core_size <= 0 or max_cycles <= 0 or max_length <= 0:
            raise Exception
    except:
        label.configure(text="One or more parameters has an invalid value")
        return

    if warriors_temp == []:
        label.configure(text="Cannot begin a match with no warriors in core")
        return
    
    if core_size < max_length * len(warriors_temp):
        label.configure(text="Core size cannot be smaller than max. warrior length * warrior count")
        return
    
    field_size = core_size
    max_cycle_count = max_cycles
    max_program_length = max_length

    warriors = deepcopy(warriors_temp)
    initialize_core()
    state_button.configure(text="View Core", state=ctk.NORMAL)
    window.destroy()
    render_queue.append(state_data) # The core viewer, if it is open, needs to be updated

# Options menu

def toggle_dark_mode():
    if ctk.get_appearance_mode() == "Light":
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")