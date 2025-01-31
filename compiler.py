# This file handles the compilation of raw warrior text data into load files
import re
import options as o

# Labels are stored in the format "name": line
labels = {}

# Defined with the EQU opcode, some are predetermined
default_constants = {
    "CORESIZE": "8000"
}
constants = {}

error_list = []

debug_enabled = False

# Stores loop data, used by preprocessing
class Loop:
    def __init__(self, start_line, end_line, repeats):
        self.start_line = start_line
        self.end_line = end_line
        self.repeats = repeats

loops = []

def compile_load_file(data, debug):
    global constants, labels, debug_enabled, error_list

    if data == []: return
    new_warrior = o.Warrior("Nameless", None, None, None, [], [])
    error_list = []
    constants = default_constants.copy()
    labels = {}

    if debug: debug_enabled = True

    debug_print("Compiler active. Processing assembly file...")

    # Preprocess raw data; eliminate comments and save labels as required
    debug_print("Preprocessing input data...")
    preprocessed_data = []
    current_line = 0
    for line in data:
        # Split the line at every instance of whitespace
        attributes = re.split("\t| ", line)

        while "" in attributes:
            attributes.remove("")
        if len(attributes) == 0:
            # Line is empty
            debug_print("- Empty line detected, ignoring...")
            continue

        if attributes[0][0] == ";":
            # Line is a comment
            if attributes[0][1:] == "name" or attributes[1] == "name":
                new_warrior.name = " ".join(attributes[1:len(attributes)])
                debug_print(f"- Name parameter identified; warrior's name is {new_warrior.name}")

            elif attributes[0][1:] == "assert" or attributes[1] == "assert":
                # Evaluate the specified assert statement
                debug_print("Assert statement identified, saving expression for evaluation...")
                new_warrior.asserts.append(" ".join(str(attribute) for attribute in attributes[1:]))

            continue

        for i in range(len(attributes)):
            # Find inline comments and eliminate them
            if attributes[i][0] != ";": continue
            
            attributes = attributes[:i]
            break

        if attributes[0].upper().split(".")[0] not in o.opcodes:
            # Identify psuedo-opcodes and labels
            match attributes[0].upper():
                case "FOR":
                    # For-loops duplicate instructions until the ROF keyword for an amount specified by the second attribute
                    if len(attributes) != 2:
                        debug_print("Compiler error detected. Aborting...")
                        error_list.append(f"Bad instruction at {line.strip()}\n(invalid FOR statement)")
                        break
                    
                    # Store loop information
                    repeats = evaluate_attribute_list(attributes, 1, current_line)[1]
                    loops.append(Loop(current_line, -1, repeats))
                    debug_print(f"- FOR loop identified; repeats: {repeats}")
                    continue

                case "ROF":
                    # Terminates the nearest active loop
                    if len(attributes) > 1:
                        debug_print("Compiler error detected. Aborting...")
                        error_list.append(f"Bad instruction at {line.strip()}\n(invalid ROF statement)")
                        break

                    loop_found = False
                    target_loop = None
                    for loop in reversed(loops):
                        if loop.end_line != -1: continue

                        loop.end_line = current_line
                        loop_found = True
                        target_loop = loop
                        break

                    if not loop_found:
                        debug_print("Compiler error detected. Aborting...")
                        error_list.append(f"Bad instruction at {line.strip()}\n(no FOR to terminate)")
                        break

                    else:
                        debug_print(f"- Termination of FOR {target_loop.repeats} detected; evaluating loop result...")
                        # Repeat all instructions in the target loop the specified number of times
                        for i in range(target_loop.repeats - 1):
                            for k in range(target_loop.start_line, target_loop.end_line):
                                preprocessed_data.append(preprocessed_data[k].copy())
                                current_line += 1

                        loops.remove(target_loop)

                    continue

                case _:
                    # If the first attribute is not an opcode or psuedo-opcode, assume it is a label
                    try:
                        int(attributes[0])
                        # Labels cannot be purely numeric
                        debug_print("Compiler error detected. Aborting...")
                        error_list.append(f"Bad instruction at {line.strip()}\n(invalid symbol)")
                        break
                    except: pass

                    if len(attributes) >= 2:
                        if attributes[1].upper() == "EQU":
                            # Defines a constant
                            if len(attributes) != 3:
                                # Invalid definition
                                debug_print("Compiler error detected. Aborting...")
                                error_list.append(f"Bad instruction at {line.strip()}\n(invalid symbol)")
                                break

                            if attributes[0] in labels.keys():
                                # Constant is already declared as a label
                                debug_print("Compiler error detected. Aborting...")
                                error_list.append(f"Bad instruction at {line.strip()}\n(symbol conflict)")
                                break

                            
                            if not attributes[0].isalnum():
                                # Constant is not alphanumeric
                                debug_print("Compiler error detected. Aborting...")
                                error_list.append(f"Bad instruction at {line.strip()}\n(invalid symbol)")
                                break

                            debug_print(f"- Constant '{attributes[0]}' defined as {attributes[2]}")
                            constants[attributes[0]] = attributes[2]
                            continue

                    # Defines a label
                    if attributes[0] in labels.keys():
                        # Label is already declared as a constant
                        debug_print("Compiler error detected. Aborting...")
                        error_list.append(f"Bad instruction at {line.strip()}\n(symbol conflict)")
                        break

                    if not attributes[0].isalnum():
                        # Label is not alphanumeric
                        debug_print("Compiler error detected. Aborting...")
                        error_list.append(f"Bad instruction at {line.strip()}\n(invalid symbol)")
                        break

                    labels[attributes[0]] = current_line
                    debug_print(f"- Label '{attributes[0]}' identified on line {current_line}")
                    attributes.pop(0)

                    if len(attributes) <= 0:
                        # Label has no further instruction
                        debug_print("Compiler error detected. Aborting...")
                        error_list.append(f"Bad instruction at {line.strip()}\n(invalid symbol)")
                        break

        preprocessed_data.append(attributes)
        current_line += 1

    # Insert all constants into the preprocessed data
    for constant in constants.keys():
        debug_print(f"- Applying constant {constant}...")
        for i in range(len(preprocessed_data)):
            for k in range(len(preprocessed_data[i])):
                if k == 0: continue # Avoid replacing opcodes, labels, and other constant declarations

                # Ensure only exact matches are replaced by checking for surrounding alphanumeric characters
                search_offset = 0
                while constant in preprocessed_data[i][k]:
                    first_char_not_alnum = False
                    last_char_not_alnum = False
                    search_string = str(preprocessed_data[i][k][search_offset:])
                    constant_location = search_string.find(constant)

                    if constant_location == -1:
                        # Constant is not present in the offset string
                        break
                    
                    if constant_location == 0:
                        # Constant is at first position in attribute
                        first_char_not_alnum = True
                    elif not search_string[constant_location - 1].isalnum():
                        # Char before the constant is not alphanumeric (whitespace or a symbol i.e. +, -, |) and it is thus safe to replace
                        first_char_not_alnum = True

                    if constant_location + len(constant) >= len(search_string):
                        # Constant is at last position in the attribute
                        last_char_not_alnum = True
                    elif not search_string[constant_location + len(constant)].isalnum():
                        # Char after the constant is not alphanumeric
                        last_char_not_alnum = True

                    if first_char_not_alnum and last_char_not_alnum:
                        # Replace the first occurrence of the constant in the substring, which should always correspond to the tested positions
                        preprocessed_data[i][k] = str(preprocessed_data[i][k][:search_offset]) + search_string.replace(constant, constants[constant], 1)
                    
                    else:
                        # Discard the checked part of the string to allow for offset searches
                        search_offset += constant_location + len(constant)
    
    debug_print(f"- Preprocessing complete, data length: " + str(len(preprocessed_data)) + " lines")

    # Read each line individually and parse it into an Instruction object
    current_line = 0
    for attributes in preprocessed_data:
        # End processing early in case of errors
        if len(error_list) > 0: break

        load_line = o.Instruction(None, None, None, None, None, None)

        debug_print("Reading line: " + str(attributes))

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
            break
        if opcode_data[0] == "LDP" or opcode_data[0] == "STP":
            # P-space is not yet implemented
            debug_print("Compiler error detected. Aborting...")
            error_list.append(f"Bad instruction at '{line.strip()}'\n(P-space not supported)")
            break

        if load_line.modifier is not None:
            debug_print(f"Valid opcode and modifier confirmed: {load_line.opcode}.{load_line.modifier}")
        else:
            debug_print(f"Valid opcode confirmed: {load_line.opcode}. No modifier declared, awaiting addressing modes to determine...")

        if len(attributes) > 1:
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
            attributes = evaluate_attribute_list(attributes, 1, current_line)
            if attributes is None:
                # Complex expression evaluation failure
                debug_print("Compiler error detected, aborting...")
                error_list.append(f"Invalid A-field expression at line {current_line + 1}")
                break

            load_line.address_1 = attributes[1]
        
        else:
            # No A-field specified
            load_line.a_mode_1 = "$"
            load_line.address_1 = 0

        # Ditto for B-field
        if len(attributes) > 2:
            b_mode = attributes[2][0:1]
            if not b_mode in o.addressing_modes:
                load_line.a_mode_2 = "$"
                debug_print("No B-field addressing mode detected, assuming relative...")
            else:
                load_line.a_mode_2 = b_mode
                attributes[2] = attributes[2][1:len(attributes[2])]

            attributes = evaluate_attribute_list(attributes, 2, current_line)
            if attributes is None:
                debug_print("Compiler error detected, aborting...")
                error_list.append(f"Invalid B-field expression at line {current_line + 1}")
                break

            load_line.address_2 = attributes[2]

        else:
            if opcode_data[0] != "DAT":
                load_line.a_mode_2 = "$"
                load_line.address_2 = 0
            else:
                # For some inexplicable reason, ICWS 94 requests single-argument DATs have it placed in their B-field
                load_line.a_mode_2 = load_line.a_mode_1
                load_line.a_mode_1 = "$"
                load_line.address_1 = 0
                load_line.address_2 = attributes[1] if len(attributes) >= 2 else 0

        if load_line.modifier is None:
            load_line.modifier = get_default_modifier(load_line)
            debug_print(f"Addressing modes used to determine opcode's modifier, result: {load_line.opcode}.{load_line.modifier}")

        if len(attributes) > 3:
            # Too many attributes!
            debug_print("Compiler error detected, aborting...")
            error_list.append(f"Bad instruction at '{line.strip()}'\n(too many parameters)")
            break

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
        
def evaluate_attribute_list(attributes : list, target : int, current_line : int):
    global error_list

    debug_print(f"Initialising expression evaluation subroutine at position {target}...")
    # Check for the type of the target attribute; pure number, single symbol, or expression
    if attributes[target][-1] == "," or len(attributes) - 1 == target:
        # Attribute is either suffixed by a comma or the last attribute, and hence either a single-attribute expression or a number
        attributes[target] = attributes[target].replace(",", "")

        target_is_numeric = True
        try: int(attributes[target])
        except: target_is_numeric = False

        if target_is_numeric:
            debug_print("- Target is an address value. No further processing required...")
            attributes[target] = int(attributes[target])
        else:
            # Target is a single symbol; check it against all known labels
            if attributes[target] in list(labels.keys()):
                # Replace the label with the relative position of the target line
                debug_print(f"- Label '{attributes[target]}' matched to instruction at line {current_line}")
                attributes[target] = labels[attributes[target]] - current_line

            else:
                # If target is not found in label list, attempt complex expression evaluation
                attributes[target] += "," # Replace removed comma
                attributes = evaluate_complex_expression(attributes, target, current_line)

    else:
        # Attribute is not terminated; begin complex expression evaluation
        attributes = evaluate_complex_expression(attributes, target, current_line)

    if attributes is not None: debug_print("- Expression evaluation complete. Result: " + str(attributes[target]))

    return attributes

def evaluate_complex_expression(attributes : list, target : int, current_line : int):
    global error_list

    expr_attributes = [attributes[target]]

    # Determine the end of the current expression for evaluation
    # If the loop completes, the end of the instruction is reached; if a comma is found, terminate early
    if expr_attributes[0][-1] != ",":
        i = 1
        while len(attributes) > target + i:
            new_attribute = attributes.pop(target + i)
            if new_attribute[-1] == ",":
                expr_attributes.append(new_attribute.replace(",", ""))
                break
            else:
                expr_attributes.append(new_attribute)
    else:
        # Expression only covers one attribute
        expr_attributes[0] = expr_attributes[0].replace(",", "")

    # Check for labels in the collected symbols
    # Iteration in inverse alphabetical order is done to prevent erroneous mapping when part of one label is equal to another
    for label in labels.keys():
        for i in range(len(expr_attributes)):
            if label in expr_attributes[i]:

                # Ensure only exact matches are replaced by checking for surrounding alphanumeric characters
                search_offset = 0
                while label in expr_attributes[i]:
                    first_char_not_alnum = False
                    last_char_not_alnum = False
                    search_string = str(expr_attributes[i][search_offset:])
                    label_location = search_string.find(label)

                    if label_location == -1:
                        # Constant is not present in the offset string
                        break
                    
                    if label_location == 0:
                        # Constant is at first position in attribute
                        first_char_not_alnum = True
                    elif not search_string[label_location - 1].isalnum():
                        # Char before the label is not alphanumeric (whitespace or a symbol i.e. +, -, |) and it is thus safe to replace
                        first_char_not_alnum = True

                    if label_location + len(label) >= len(search_string):
                        # Constant is at last position in the attribute
                        last_char_not_alnum = True
                    elif not search_string[label_location + len(label)].isalnum():
                        # Char after the label is not alphanumeric
                        last_char_not_alnum = True

                    if first_char_not_alnum and last_char_not_alnum:
                        # Replace the first occurrence of the label in the substring
                        debug_print(f"- Label '{label}' matched to instruction at line {current_line}")
                        expr_attributes[i] = str(expr_attributes[i][:search_offset]) + search_string.replace(label, str(labels[label] - current_line), 1)
                    
                    else:
                        # Discard the checked part of the string to allow for offset searches
                        search_offset += label_location + len(label)

    expression = " ".join(expr_attributes)

    # Map Redcode operands, which are identical to C (&&, ||, !), to Python operands (and, or, not)
    expression = expression.replace("&&", " and ")
    expression = expression.replace("||", " or ")
    expression = expression.replace("!", "not ")

    # Evaluate and return the modified attribute list
    try:
        attributes[target] = int(eval(expression))
        debug_print(f"- Expression {expression} evaluated; result: {attributes[target]}")
        return attributes

    except Exception as e:
        debug_print(f"- Expression evaluation ERROR at {expression}: " + str(e))
        # The compiler recognises this as an evaluation failure
        return None
    
def is_assert_valid(expression : str):
    # Called on apply of a setup; if any of these 
    pass

# For use as debug symbol
def debug_print(text):
    if debug_enabled:
        print(text)
