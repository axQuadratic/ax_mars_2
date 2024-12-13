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
    orange = (255, 150, 0)
    purple = (110, 0, 255)
    pink = (255, 110, 230)
    gray = (200, 200, 200)
    white = (255, 255, 255)
    black = (10, 10, 10)
    highlight = (31, 83, 141)

# RGB to hex algorithm straight from Stackoverflow
def get_tile_hex_color(color : str):
    color = color.removeprefix("cross_")
    rgb = tile_colors[color].value
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])

# Quick algorithm for getting a main colour based on a number
def get_tile_color_from_id(id : int, cross : bool = False):
    color = [v.name for v in tile_colors][id % 8]
    if cross: color = "cross_" + color
    return color

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
    def __init__(self, opcode : str, modifier : str, a_mode_1 : str, address_1, a_mode_2 : str, address_2):
        self.opcode = opcode
        self.modifier = modifier
        self.a_mode_1 = a_mode_1
        self.address_1 = address_1
        self.a_mode_2 = a_mode_2
        self.address_2 = address_2

    # Necessary to allow comparisons between instances by attributes
    def __eq__(self, other):
        c1 = self.opcode == other.opcode and self.modifier == other.modifier and self.a_mode_1 == other.a_mode_1
        c2 = self.address_1 == other.address_1 and self.a_mode_2 == other.a_mode_2 and self.address_2 == other.address_2
        return c1 and c2

class Warrior:
    def __init__(self, name : str, id : int, color : str, raw_data : list, load_file : list):
        self.name = name
        self.id = id
        self.color = color
        self.raw_data = raw_data
        self.load_file = load_file

class Process:
    def __init__(self, location : int, warrior : int):
        self.location = location
        self.warrior = warrior
        self.dying = False

class Tile:
    def __init__(self, warrior : int, color : str, instruction : Instruction, read_marked : bool, highlighted : bool):
        self.warrior = warrior
        self.color = color
        self.instruction = instruction
        self.read_marked = read_marked
        self.highlighted = highlighted

    # See Instruction
    def __eq__(self, other):
        c1 = self.warrior == other.warrior and self.color == other.color and self.instruction == other.instruction
        c2 = self.read_marked == other.read_marked and self.highlighted == other.highlighted
        return c1 and c2
    
    def __ne__(self, other):
        c1 = self.warrior != other.warrior or self.color != other.color or self.instruction != other.instruction
        c2 = self.read_marked != other.read_marked or self.highlighted != other.highlighted
        return c1 or c2

# This is declared here, so it can be accessed by other files
root = ctk.CTk()

user_config = {}

play_speed = 1
paused = True
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
update_requested = False
sim_completed = False
program_closing = False

speed_levels = [1, 5, 10, 50, 100, 250, 500, 1000, 2000, 5000]
max_speed_enabled = False
deghost_button_enabled = False

def initialize_core():
    global state_data, process_queue, prev_state_data, cur_cycle

    # Initialize a new core with all warriors and parameters
    state_data = [Tile(None, "black", Instruction("DAT", "F", "$", 0, "$", 0), False, False) for i in range(field_size)]
    process_queue = []
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
            state_data[i % field_size] = Tile(None, "cross_" + warrior.color, line, False, False)
            i += 1

        # Add warrior's process queue to main queue
        process_queue.append([Process(warrior_pos, warrior.id)])

    # All negative numbers in the core are converted to equivalent positives, as ICWS 94 requires
    for tile in state_data:
        if tile.instruction.address_1 < 0:
            tile.instruction.address_1 = field_size - (tile.instruction.address_1 * -1)
        if tile.instruction.address_2 < 0:
            tile.instruction.address_2 = field_size - (tile.instruction.address_2 * -1)

def parse_instruction_to_text(instruction : Instruction):
    return f"{instruction.opcode}.{instruction.modifier} {instruction.a_mode_1}{instruction.address_1}, {instruction.a_mode_2}{instruction.address_2}"

def close_all_threads():
    global program_closing

    # For terminating all active processes on program exit
    program_closing = True
    root.destroy()

# Options menu

def toggle_dark_mode():
    # Changing dark mode options does not actually require a program restart; however changing theme does, and I want consistency
    if ctk.get_appearance_mode() == "Light":
        user_config["dark_mode_enabled"] = True
    else:
        user_config["dark_mode_enabled"] = False

def toggle_deghost():
    global deghost_button_enabled

    deghost_button_enabled = not deghost_button_enabled
    user_config["deghost_button_enabled"] = deghost_button_enabled

def set_theme(theme : str):
    user_config["selected_theme"] = theme