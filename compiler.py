# This file handles the compilation of raw warrior text data into load files
# It is also the file that handles final parsing and execution of load file data
import re
import options as o

def compile_load_file(data):
    if data == []: return
    load_data = []
    error_list = ""

    # Read each line individually and parse it into an Instruction object
    for line in data:
        load_line = o.Instruction(None, None, None, None, None, None, None)

        # Split the line at every instance of whitespace
        attributes = re.split("\t| ", line)

        while "" in attributes:
            attributes.remove("")
        if len(attributes) > 4 or (len(attributes) == 4 and attributes[0] in o.opcodes):
            # Too many attributes!
            load_line = o.Instruction(None, "DAT", ".F", "#", 0, "#", 0)
            error_list += f"Bad instruction at '{line}' (too many attributes)"
            break
        if len(attributes == 4):
            load_line.label = attributes[0]
            

        load_data.append(load_line)

    print(load_data, error_list)

def get_default_modifier(instruction : o.Instruction):
    # If no modifer is specifed in raw data, it is determined according to these rules
    # These are defined arbitrarily in ICWS 94
    match instruction.opcode:
        case "MOV" | "SEQ" | "SNE" | "CMP":
            if instruction.a_mode_1 == "#":
                return ".AB"
            elif instruction.a_mode_2 == "#":
                return ".B"
            else:
                return ".I"
        case "ADD" | "SUB" | "MUL" | "DIV" | "MOD":
            if instruction.a_mode_1 == "#":
                return ".AB"
            elif instruction.a_mode_2 == "#":
                return ".B"
            else:
                return ".F"
        case "SLT" | "LDP" | "STP":
            if instruction.a_mode_1 == "#":
                return ".AB"
            else:
                return ".B"
        case "DAT" | "NOP":
            return ".F"
        case _:
            return ".B"