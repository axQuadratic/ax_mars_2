# This file handles the compilation of raw warrior text data into load files
# It is also the file that handles final parsing and execution of load file data
import re
import options as o

# For easy access to label data
class Label:
    def __init__(self, name, line):
        self.name = name
        self.line = line

labels = []

debug_enabled = False

def compile_load_file(data, debug):
    global labels, debug_enabled

    if data == []: return
    load_data = []
    error_list = []

    if debug: debug_enabled = True

    debug_print("Compiler active. Processing assembly file...")

    # Read each line individually and parse it into an Instruction object
    current_line = 0
    for line in data:
        load_line = o.Instruction(None, None, None, None, None, None, None)

        debug_print("Reading line: " + line)

        # Split the line at every instance of whitespace
        attributes = re.split("\t| ", line)

        while "" in attributes:
            attributes.remove("")
        if len(attributes) == 0:
            # Line is empty
            debug_print("Line is empty, continuing...")
            continue
        if len(attributes) > 4:
            # Too many attributes!
            debug_print("Compiler error detected. Aborting...")
            error_list.append(f"Bad instruction at '{line.strip()}' (too many attributes)")
            load_data.append(load_line)
            continue
        
        initial_data = attributes[0].upper().split(".")
        # Insert every attribute into the instruction object in order
        if initial_data[0] not in o.opcodes:
            # Label is present
            if attributes[0].isnumeric():
                # Labels cannot be purely numeric
                debug_print("Detected label is purely numeric. Ignoring...")
            else:
                load_line.label = attributes[0]
                labels.append(Label(load_line.label, current_line))
                debug_print("Line has label: " + load_line.label)
            attributes.pop(0) # To ensure consistency with labelless instructions
            if len(attributes) == 0:
                # Label has no instruction
                debug_print("Compiler error detected. Aborting...")
                error_list.append(f"Bad instruction at '{line.strip()}' (invalid opcode)")
                load_data.append(load_line)
                continue

        opcode_data = attributes[0].upper().split(".")
        # Extract the modifier from the opcode
        load_line.opcode = opcode_data[0]
        if len(opcode_data) == 2:
            # Modifier is determined later if none is declared
            load_line.modifier = opcode_data[1]
        if opcode_data[0] not in o.opcodes or (len(opcode_data) > 1 and opcode_data[1] not in o.modifiers) or len(opcode_data) > 2:
            # Bad opcode
            debug_print("Compiler error detected. Aborting...")
            error_list.append(f"Bad instruction at '{line.strip()}' (invalid opcode)")
            load_data.append(load_line)
            continue

        if load_line.modifier is not None:
            debug_print(f"Valid opcode and modifier confirmed: {load_line.opcode}.{load_line.modifier}")
        else:
            debug_print(f"Valid opcode confirmed: {load_line.opcode}. No modifier declared, processing...")

        # Extract addressing modes from adresses
        if len(attributes) >= 2:
            a_mode_1 = attributes[1][0:1]
            att_1 = None
        else:
            # All other address-related blocks fall through if these are set here 
            a_mode_1 = "$" if load_line.opcode != "DAT" else "#"
            att_1 = "0,"
            debug_print(f"No A-field specified, assuming {a_mode_1}0...")
        
        second_attribute_unset = False
        if len(attributes) >= 3:
            a_mode_2 = attributes[2][0:1]
            att_2 = None
        else:
            a_mode_2 = "$" if load_line.opcode != "DAT" else "#"
            att_2 = "0"
            second_attribute_unset = True
            debug_print(f"No B-field specified, assuming {a_mode_2}0...")

        if a_mode_1 not in o.addressing_modes:
            # No addressing mode is present
            debug_print(f"No addressing mode detected in A-field. Assuming {'relative' if load_line.opcode != 'DAT' else 'immediate'}...")
            a_mode_1 = "$" if load_line.opcode != "DAT" else "#"
            att_1 = attributes[1]
        elif att_1 is None:
            att_1 = attributes[1][1:len(attributes[1])]
        if a_mode_2 not in o.addressing_modes:
            debug_print(f"No addressing mode detected in B-field. Assuming {'relative' if load_line.opcode != 'DAT' else 'immediate'}...")
            a_mode_2 = "$" if load_line.opcode != "DAT" else "#"
            att_2 = attributes[2]
        elif att_2 is None:
            att_2 = attributes[2][1:len(attributes[2])]

        debug_print(f"Field expressions determined as {a_mode_1}{att_1} {a_mode_2}{att_2}")

        # Adresses must be comma separated according to ICWS 94
        if list(att_1)[-1] != "," and not second_attribute_unset:
            debug_print("Compiler error detected. Aborting...")
            error_list.append(f"Bad instruction at '{line.strip()}' (invalid adress)")
            load_data.append(load_line)
            continue

        # Remove trailing commas
        att_1 = att_1.replace(",", "")
        att_2 = att_2.replace(",", "")

        load_line.a_mode_1 = a_mode_1
        load_line.address_1 = att_1
        load_line.a_mode_2 = a_mode_2
        load_line.address_2 = att_2

        if load_line.modifier is None:
            # Rules for default modifiers are arbitrary and defined in ICWS 94
            load_line.modifier = get_default_modifier(load_line)
            debug_print(f"Processing has determined opcode's modifier, result: {load_line.opcode}.{load_line.modifier}")

        load_data.append(load_line)
        debug_print(f"Line completed. Load file output: {load_line.opcode}.{load_line.modifier} {load_line.a_mode_1}{load_line.address_1}, {load_line.a_mode_2}{load_line.address_2}")

        current_line += 1

    if error_list == []:
        debug_print("Compiler operation completed successfully.")
    else:
        debug_print(f"Compiler operation completed. {len(error_list)} invalid lines ignored.")

    return load_data, error_list

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

# For use as debug symbol
def debug_print(text):
    if debug_enabled:
        print(text)