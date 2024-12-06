# This file handles the compilation of raw warrior text data into load files
# It is also the file that handles final parsing and execution of load file data
import re
import options as o

# For easy access to label data
class Label:
    def __init__(self, name, line):
        self.name = name
        self.line = line

    def __eq__(self, other : str):
        return self.name == other
    
    def __ne__(self, other : str):
        return self.name != other

labels = []

# Not currently implemented
constants = {
    "CORESIZE": 8000
}

debug_enabled = False

def compile_load_file(data, debug):
    global labels, debug_enabled

    if data == []: return
    new_warrior = o.Warrior("Nameless", None, None, None, [])
    error_list = []

    if debug: debug_enabled = True

    debug_print("Compiler active. Processing assembly file...")

    # Unimplemented label-related code for future use
    """
    if initial_data[0] not in o.opcodes:
        # Label is present
        if attributes[0].isnumeric():
            # Labels cannot be purely numeric
            debug_print("Detected label is purely numeric. Ignoring...")
        else:
            load_line.label = attributes[0]
            labels.append(Label(load_line.label, current_line))
            debug_print("Line has label: " + load_line.label)
        if len(attributes) == 1:
            # Label has no instruction
            debug_print("Compiler error detected. Aborting...")
            error_list.append(f"Bad instruction at '{line.strip()}'\n(invalid opcode)")
            new_warrior.load_file.append(load_line)
            continue
        attributes.pop(0) # To ensure consistency with labelless instructions
    """

    # Read each line individually and parse it into an Instruction object
    current_line = 0
    for line in data:
        load_line = o.Instruction(None, None, None, None, None, None)

        debug_print("Reading line: " + line)

        # Split the line at every instance of whitespace
        attributes = re.split("\t| ", line)

        while "" in attributes:
            attributes.remove("")
        if len(attributes) == 0:
            # Line is empty
            debug_print("Line is empty, continuing...")
            continue

        if attributes[0][0] == ";":
            # Line is a comment
            if attributes[0][1:len(attributes[0])] == "name":
                new_warrior.name = " ".join(attributes[1:len(attributes)])
            elif attributes[1] == "name":
                new_warrior.name = " ".join(attributes[2:len(attributes)])
            else:
                continue

            debug_print(f";name parameter identified; warrior's name is {new_warrior.name}")
            continue

        # Insert every attribute into the instruction object in order
        opcode_data = attributes[0].upper().split(".")
        # Extract the modifier from the opcode
        load_line.opcode = opcode_data[0]
        if len(opcode_data) == 2:
            # Modifier is determined later if none is declared
            load_line.modifier = opcode_data[1]
        if opcode_data[0] not in o.opcodes or (len(opcode_data) > 1 and opcode_data[1] not in o.modifiers) or len(opcode_data) > 2:
            # Bad opcode
            debug_print("Compiler error detected. Aborting...")
            error_list.append(f"Bad instruction at '{line.strip()}'\n(invalid opcode)")
            new_warrior.load_file.append(load_line)
            continue
        if opcode_data[0] == "LDP" or opcode_data[0] == "STP":
            # P-space is not yet implemented
            debug_print("Compiler error detected. Aborting...")
            error_list.append(f"Bad instruction at '{line.strip()}'\n(P-space not supported)")

        if load_line.modifier is not None:
            debug_print(f"Valid opcode and modifier confirmed: {load_line.opcode}.{load_line.modifier}")
        else:
            debug_print(f"Valid opcode confirmed: {load_line.opcode}. No modifier declared, awaiting addressing modes to determine...")

        # Extract the A-field addressing mode
        a_mode = attributes[1][0:1]
        if not a_mode in o.addressing_modes:
            # None is declared; use default
            load_line.a_mode_1 = "$"
            debug_print("No A-field addressing mode detected, assuming relative...")
        else:
            load_line.a_mode_1 = a_mode
            attributes[1] = attributes[1][1:len(attributes[1])]

        # Evaluates any expressions or labels in the following addresses
        attributes = evaluate_attribute_list(attributes, 1)

        # Ditto for B-field unless none is specified
        if len(attributes) > 2:
            b_mode = attributes[2][0:1]
            if not b_mode in o.addressing_modes:
                load_line.a_mode_2 = "$"
                debug_print("No B-field addressing mode detected, assuming relative...")
            else:
                load_line.a_mode_2 = a_mode
                attributes[2] = attributes[2][1:len(attributes[2])]

            attributes = evaluate_attribute_list(attributes, 2)

            # Assign the processed values to their appropariate locations
            load_line.address_1 = attributes[1]
            load_line.address_2 = attributes[2]

        else:
            # No B-field specified
            if opcode_data[0] != "DAT":
                load_line.address_1 = attributes[1]
                load_line.a_mode_2 = "$"
                load_line.address_2 = 0
            else:
                # For some inexplicable reason, ICWS 94 requests single-argument DATs have it placed in their B-field
                load_line.a_mode_2 = load_line.a_mode_1
                load_line.a_mode_1 = "$"
                load_line.address_1 = 0
                load_line.address_2 = attributes[1]

        if load_line.modifier is None:
            load_line.modifier = get_default_modifier(load_line)
            debug_print(f"Addressing modes used to determine opcode's modifier, result: {load_line.opcode}.{load_line.modifier}")

        new_warrior.load_file.append(load_line)
        debug_print(f"Line completed. Load file output: " + o.parse_instruction_to_text(load_line))

        current_line += 1

    if error_list == []:
        debug_print("Compiler operation completed successfully.")
    else:
        debug_print(f"Compiler operation completed. {len(error_list)} invalid lines ignored.")

    return new_warrior, error_list

def get_default_modifier(instruction : o.Instruction):
    # If no modifer is specifed in raw data, it is determined according to these rules
    # These are defined arbitrarily in ICWS 94
    match instruction.opcode:
        case "MOV" | "SEQ" | "SNE" | "CMP":
            if instruction.a_mode_1 == "#":
                return "AB"
            elif instruction.a_mode_2 == "#":
                return "B"
            else:
                return "I"
        case "ADD" | "SUB" | "MUL" | "DIV" | "MOD":
            if instruction.a_mode_1 == "#":
                return "AB"
            elif instruction.a_mode_2 == "#":
                return "B"
            else:
                return "F"
        case "SLT" | "LDP" | "STP":
            if instruction.a_mode_1 == "#":
                return "AB"
            else:
                return "B"
        case "DAT" | "NOP":
            return "F"
        case _:
            return "B"
        
def evaluate_attribute_list(attributes : list, target : int):
    debug_print(f"Initialising expression evaluation subroutine at position {target}...")
    # Check for the type of the target attribute; pure number, single label, or expression
    if attributes[target][-1] == "," or len(attributes) - 1 <= target:
        # Attribute is either suffixed by a comma or the last attribute, and hence either a single label or a number
        attributes[target] = attributes[target].replace(",", "")

        target_is_numeric = True
        try: 
            int(attributes[target])
        except:
            target_is_numeric = False

        if target_is_numeric:
            debug_print("EXEVAL: Target is an address value. No further processing required...")
            attributes[target] = int(attributes[target])
        else:
            # Target is a single label; check it against all known labels
            pass

    debug_print("EXEVAL: Expression evaluation complete. Result: " + str(attributes[target]))
    return attributes

# For use as debug symbol
def debug_print(text):
    if debug_enabled:
        print(text)