# This file handles the compilation of raw warrior text data into load files
# It is also the file that handles final parsing and execution of load file data
import options as o

def compile_load_file(data):
    pass

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