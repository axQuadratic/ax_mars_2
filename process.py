# This file handles the underlying simulation part of the program

import options as o
import math
from time import sleep
from copy import copy

def simulation_clock(single_step : bool = False):
    # Executes every interval given by play speed; triggers match turn calculations
    while True:
        cycle_count = 1

        if not single_step:
            # Simulation is running normally
            if o.max_speed_enabled:
                # Immediately run the entire simulation
                cycle_count = o.match_options["max_cycle_count"] - o.cur_cycle
                sleep(1)
            elif o.play_speed < 2:
                sleep(1 / o.play_speed)
            else:
                # Above 5x speed, multiple instructions are run at once to decrease rendering demand
                cycle_count = math.ceil(o.play_speed / 2)
                sleep(0.5)
                
            if o.program_closing: break
            if o.paused or o.sim_completed: continue

        if o.cur_cycle + cycle_count > o.match_options["max_cycle_count"]:
            cycle_count = o.match_options["max_cycle_count"] - o.cur_cycle

        # Reset all read highlights in state data
        for i in range(len(o.state_data)):
            o.state_data[i].read_marked = False

        for k in range(cycle_count):
            # Execute instructions as required; each warrior executes one
            for i in range(len(o.process_queue)):
                try:
                    o.state_data, o.process_queue[i] = execute_process(o.process_queue[i], o.state_data)

                    if o.process_queue[i] == []:
                        # Warrior has no remaining processes and is eliminated
                        o.warriors_temp.pop(i)
                        o.process_queue.pop(i)
                        for tile in o.state_data:
                            if tile.warrior != i: continue
                            tile.color = "cross_" + tile.color.removeprefix("cross_")

                        # Only one warrior remains, and is the winner
                        if len(o.warriors_temp) == 1:
                            o.sim_completed = True
                
                # Since it is not possible to change the range of an active for loop, simply ignore the excess
                except IndexError: continue

        o.update_requested = True
        o.cur_cycle += cycle_count

        if o.cur_cycle >= o.match_options["max_cycle_count"]:
            # End the simulation
            o.sim_completed = True

        if single_step:
            # Advance button only executes one cycle
            break

def execute_process(queue : list, state : list):
    # The main execution function

    process = queue.pop(0)

    # Apply read marker to the currently targeted instruction
    state[process.location].warrior = process.warrior
    state[process.location].color = o.get_tile_color_from_id(process.warrior)
    # Add read highlight to new process location unless max speed is enabled
    if not o.max_speed_enabled: state[process.location].read_marked = True

    state, new_processes = evaluate_instruction(state, state[process.location].instruction, process)

    # Add the updated processes back to the queue unless they has been killed
    for new_process in new_processes:
        if new_process.dying: continue
        queue.append(new_process)

    return state, queue

def evaluate_instruction(state : list, instruction : o.Instruction, cur_process : o.Process):
    # The main execution function
    location_1 = get_absolute_core_location(instruction.a_mode_1, instruction.address_1, cur_process.location)
    location_2 = get_absolute_core_location(instruction.a_mode_2, instruction.address_2, cur_process.location)

    # Stores the active process and any processes created during execution
    new_processes = [cur_process]

    match instruction.opcode:
        case "MOV":
            # Copies fields of the source (loc1) into fields of the target (loc2)
            match instruction.modifier:
                case "A":
                    # A to A
                    state[location_2].instruction.a_mode_1 = state[location_1].instruction.a_mode_1
                    state[location_2].instruction.address_1 = state[location_1].instruction.address_1
                case "B":
                    # B to B
                    state[location_2].instruction.a_mode_2 = state[location_1].instruction.a_mode_2
                    state[location_2].instruction.address_2 = state[location_1].instruction.address_2
                case "AB":
                    # A to B
                    state[location_2].instruction.a_mode_2 = state[location_1].instruction.a_mode_1
                    state[location_2].instruction.address_2 = state[location_1].instruction.address_1
                case "BA":
                    # B to A
                    state[location_2].instruction.a_mode_1 = state[location_1].instruction.a_mode_2
                    state[location_2].instruction.address_1 = state[location_1].instruction.address_2
                case "F":
                    # A to A + B to B
                    state[location_2].instruction.a_mode_1 = state[location_1].instruction.a_mode_1
                    state[location_2].instruction.address_1 = state[location_1].instruction.address_1
                    state[location_2].instruction.a_mode_2 = state[location_1].instruction.a_mode_2
                    state[location_2].instruction.address_2 = state[location_1].instruction.address_2
                case "X":
                    # A to B + B to A
                    state[location_2].instruction.a_mode_1 = state[location_1].instruction.a_mode_2
                    state[location_2].instruction.address_1 = state[location_1].instruction.address_2
                    state[location_2].instruction.a_mode_2 = state[location_1].instruction.a_mode_1
                    state[location_2].instruction.address_2 = state[location_1].instruction.address_1
                case "I":
                    # Whole instruction
                    state[location_2].instruction = copy(state[location_1].instruction)

            if state[location_2].color != state[cur_process.location].color:
                state[location_2].color = "cross_" + state[cur_process.location].color.removeprefix("cross_")

        case "DAT":
            # Kills the current process
            cur_process.dying = True
            return state, new_processes

        case "ADD":
            # Adds the number in the source to the address in the destination
            # Note that for all math operations, the source is always the current instruction unless indirect addressing is used
            match instruction.modifier:
                case "A":
                    state[location_2].instruction.address_1 += state[location_1].instruction.address_1
                case "B":
                    state[location_2].instruction.address_2 += state[location_1].instruction.address_2
                case "AB":
                    state[location_2].instruction.address_2 += state[location_1].instruction.address_1
                case "BA":
                    state[location_2].instruction.address_1 += state[location_1].instruction.address_2
                case "F" | "I":
                    state[location_2].instruction.address_1 += state[location_1].instruction.address_1
                    state[location_2].instruction.address_2 += state[location_1].instruction.address_2
                case "X":
                    state[location_2].instruction.address_1 += state[location_1].instruction.address_2
                    state[location_2].instruction.address_2 += state[location_1].instruction.address_1

        case "SUB":
            # Subtracts the number in the source from the address in the target
            match instruction.modifier:
                case "A":
                    state[location_2].instruction.address_1 -= state[location_1].instruction.address_1
                case "B":
                    state[location_2].instruction.address_2 -= state[location_1].instruction.address_2
                case "AB":
                    state[location_2].instruction.address_2 -= state[location_1].instruction.address_1
                case "BA":
                    state[location_2].instruction.address_1 -= state[location_1].instruction.address_2
                case "F" | "I":
                    state[location_2].instruction.address_1 -= state[location_1].instruction.address_1
                    state[location_2].instruction.address_2 -= state[location_1].instruction.address_2
                case "X":
                    state[location_2].instruction.address_1 -= state[location_1].instruction.address_2
                    state[location_2].instruction.address_2 -= state[location_1].instruction.address_1

        case "MUL":
            # Multiplies the target by the source
            match instruction.modifier:
                case "A":
                    state[location_2].instruction.address_1 *= state[location_1].instruction.address_1
                case "B":
                    state[location_2].instruction.address_2 *= state[location_1].instruction.address_2
                case "AB":
                    state[location_2].instruction.address_2 *= state[location_1].instruction.address_1
                case "BA":
                    state[location_2].instruction.address_1 *= state[location_1].instruction.address_2
                case "F" | "I":
                    state[location_2].instruction.address_1 *= state[location_1].instruction.address_1
                    state[location_2].instruction.address_2 *= state[location_1].instruction.address_2
                case "X":
                    state[location_2].instruction.address_1 *= state[location_1].instruction.address_2
                    state[location_2].instruction.address_2 *= state[location_1].instruction.address_1

        case "DIV":
            # Divides the target by the source
            # Note that it is always integer division, and division by 0 kills the process
            try:
                match instruction.modifier:
                    case "A":
                        state[location_2].instruction.address_1 //= state[location_1].instruction.address_1
                    case "B":
                        state[location_2].instruction.address_2 //= state[location_1].instruction.address_2
                    case "AB":
                        state[location_2].instruction.address_2 //= state[location_1].instruction.address_1
                    case "BA":
                        state[location_2].instruction.address_1 //= state[location_1].instruction.address_2
                    case "F" | "I":
                        state[location_2].instruction.address_1 //= state[location_1].instruction.address_1
                        state[location_2].instruction.address_2 //= state[location_1].instruction.address_2
                    case "X":
                        state[location_2].instruction.address_1 //= state[location_1].instruction.address_2
                        state[location_2].instruction.address_2 //= state[location_1].instruction.address_1
            except ZeroDivisionError:
                cur_process.dying = True
                return state, new_processes

        case "MOD":
            # Performs modulo operation using the target and the source
            try:
                match instruction.modifier:
                    case "A":
                        state[location_2].instruction.address_1 %= state[location_1].instruction.address_1
                    case "B":
                        state[location_2].instruction.address_2 %= state[location_1].instruction.address_2
                    case "AB":
                        state[location_2].instruction.address_2 %= state[location_1].instruction.address_1
                    case "BA":
                        state[location_2].instruction.address_1 %= state[location_1].instruction.address_2
                    case "F" | "I":
                        state[location_2].instruction.address_1 %= state[location_1].instruction.address_1
                        state[location_2].instruction.address_2 %= state[location_1].instruction.address_2
                    case "X":
                        state[location_2].instruction.address_1 %= state[location_1].instruction.address_2
                        state[location_2].instruction.address_2 %= state[location_1].instruction.address_1
            except ZeroDivisionError:
                cur_process.dying = True
                return state, new_processes

        case "JMP":
            # Jumps to the A-field address
            cur_process.location = location_1
            return state, new_processes
        
        case "JMZ":
            # Jumps to the A-field address only if the value of the target is 0
            check_passed = False
            match instruction.modifier:
                case "A" | "AB":
                    if state[location_2].instruction.address_1 == 0:
                        check_passed = True
                case "B" | "BA":
                    if state[location_2].instruction.address_2 == 0:
                        check_passed = True
                case "F" | "X" | "I":
                    if state[location_2].instruction.address_1 == 0 and state[location_2].instruction.address_2 == 0:
                        check_passed = True
            if check_passed:
                cur_process.location = location_1
                return state, new_processes
            
        case "JMN":
            # Jumps if target is not 0; the opposite of JMZ
            check_passed = False
            match instruction.modifier:
                case "A" | "AB":
                    if state[location_2].instruction.address_1 != 0:
                        check_passed = True
                case "B" | "BA":
                    if state[location_2].instruction.address_2 != 0:
                        check_passed = True
                case "F" | "X" | "I":
                    if state[location_2].instruction.address_1 != 0 or state[location_2].instruction.address_2 != 0:
                        check_passed = True
            if check_passed:
                cur_process.location = location_1
                return state, new_processes

        case "DJN":
            # Identical to JMN except the target number is first decemented by 1
            check_passed = False
            match instruction.modifier:
                case "A" | "AB":
                    state[location_2].instruction.address_1 -= 1
                    if state[location_2].instruction.address_1 != 0:
                        check_passed = True
                case "B" | "BA":
                    state[location_2].instruction.address_2 -= 1
                    if state[location_2].instruction.address_2 != 0:
                        check_passed = True
                case "F" | "X" | "I":
                    state[location_2].instruction.address_1 -= 1
                    state[location_2].instruction.address_2 -= 1
                    if state[location_2].instruction.address_1 != 0 or state[location_2].instruction.address_2 != 0:
                        check_passed = True
            if check_passed:
                cur_process.location = location_1
                return state, new_processes

        case "SPL":
            # Creates a new process at the target location
            new_processes.append(o.Process(location_1, cur_process.warrior))

        case "SEQ" | "CMP":
            # Compares the instructions at the A- and B-fields; skips the next instruction if they are equal
            check_passed = False
            match instruction.modifier:
                case "A":
                    if state[location_1].instruction.address_1 == state[location_2].instruction.address_1:
                        check_passed = True
                case "B":
                    if state[location_1].instruction.address_2 == state[location_2].instruction.address_2:
                        check_passed = True
                case "AB":
                    if state[location_1].instruction.address_1 == state[location_2].instruction.address_2:
                        check_passed = True
                case "BA":
                    if state[location_1].instruction.address_2 == state[location_2].instruction.address_1:
                        check_passed = True
                case "F":
                    if state[location_1].instruction.address_1 == state[location_2].instruction.address_1 and state[location_1].instruction.address_2 == state[location_2].instruction.address_2:
                        check_passed = True
                case "X":
                    if state[location_1].instruction.address_1 == state[location_2].instruction.address_2 and state[location_1].instruction.address_2 == state[location_2].instruction.address_1:
                        check_passed = True
                case "I":
                    if state[location_1].instruction == state[location_2].instruction:
                        check_passed = True
            if check_passed:
                cur_process.location += 2
                cur_process.location %= o.match_options["field_size"]
                return state, new_processes

        case "SNE":
            # Inverse of SEQ/CMP; skips if compared instructions are not equal
            check_passed = False
            match instruction.modifier:
                case "A":
                    if state[location_1].instruction.address_1 != state[location_2].instruction.address_1:
                        check_passed = True
                case "B":
                    if state[location_1].instruction.address_2 != state[location_2].instruction.address_2:
                        check_passed = True
                case "AB":
                    if state[location_1].instruction.address_1 != state[location_2].instruction.address_2:
                        check_passed = True
                case "BA":
                    if state[location_1].instruction.address_2 != state[location_2].instruction.address_1:
                        check_passed = True
                case "F":
                    if state[location_1].instruction.address_1 != state[location_2].instruction.address_1 or state[location_1].instruction.address_2 != state[location_2].instruction.address_2:
                        check_passed = True
                case "X":
                    if state[location_1].instruction.address_1 != state[location_2].instruction.address_2 or state[location_1].instruction.address_2 != state[location_2].instruction.address_1:
                        check_passed = True
                case "I":
                    if state[location_1].instruction != state[location_2].instruction:
                        check_passed = True
            if check_passed:
                cur_process.location += 2
                cur_process.location %= o.match_options["field_size"]
                return state, new_processes
            
        case "SLT":
            # Performs SEQ/CMP/SNE skip if the source value is less than the target
            check_passed = False
            match instruction.modifier:
                case "A":
                    if state[location_1].instruction.address_1 < state[location_2].instruction.address_1:
                        check_passed = True
                case "B":
                    if state[location_1].instruction.address_2 < state[location_2].instruction.address_2:
                        check_passed = True
                case "AB":
                    if state[location_1].instruction.address_1 < state[location_2].instruction.address_2:
                        check_passed = True
                case "BA":
                    if state[location_1].instruction.address_2 < state[location_2].instruction.address_1:
                        check_passed = True
                case "F" | "I":
                    if state[location_1].instruction.address_1 < state[location_2].instruction.address_1 or state[location_1].instruction.address_2 < state[location_2].instruction.address_2:
                        check_passed = True
                case "X":
                    if state[location_1].instruction.address_1 < state[location_2].instruction.address_2 or state[location_1].instruction.address_2 < state[location_2].instruction.address_1:
                        check_passed = True
            if check_passed:
                cur_process.location += 2
                cur_process.location %= o.match_options["field_size"]
                return state, new_processes

        case "NOP" | "_":
            # No operation
            pass

    # Move the process forward one step
    cur_process.location += 1
    cur_process.location %= o.match_options["field_size"]
        
    return state, new_processes

def get_absolute_core_location(mode : str, value : int, origin : int):
    # Converts an addressing mode-value pair to an absolute value
    next_location = (origin + value) % o.match_options["field_size"]

    match mode:
        case "#":
            # Immediate addressing always evaluates to $0
            return origin
        case "$":
            # Relative
            return next_location
        case "*":
            # A-field indirect
            target = o.state_data[next_location].instruction.address_1
            return get_absolute_core_location("$", target, next_location)
        case "@":
            # B-field indirect
            target = o.state_data[next_location].instruction.address_2
            return get_absolute_core_location("$", target, next_location)
        case "{":
            # Predecremented A-field indirect
            target = o.state_data[next_location].instruction.address_1
            o.state_data[next_location].instruction.address_1 -= 1
            return get_absolute_core_location("$", target, next_location)
        case "<":
            # Predecremented B-field indirect
            target = o.state_data[next_location].instruction.address_2
            o.state_data[next_location].instruction.address_2 -= 1
            return get_absolute_core_location("$", target, next_location)
        case "}":
            # Postincremented A-field indirect
            target = o.state_data[next_location].instruction.address_1
            value = get_absolute_core_location("$", target, next_location)
            o.state_data[next_location].instruction.address_1 += 1
            return value
        case ">":
            # Postincremented B-field indirect
            target = o.state_data[next_location].instruction.address_2
            value = get_absolute_core_location("$", target, next_location)
            o.state_data[next_location].instruction.address_2 += 1
            return value
        