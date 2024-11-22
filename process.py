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
                cycle_count = o.max_cycle_count - o.cur_cycle
                sleep(1)
            elif o.play_speed < 2:
                sleep(1 / o.play_speed)
            else:
                # Above 5x speed, multiple instructions are run at once to decrease rendering demand
                cycle_count = math.ceil(o.play_speed / 2)
                sleep(0.5)
            if o.paused or o.sim_completed: continue

        if o.cur_cycle + cycle_count > o.max_cycle_count:
            cycle_count = o.max_cycle_count - o.cur_cycle

        # Reset all read highlights in state data
        for i in range(len(o.state_data)):
            o.state_data[i].read_marked = False

        for i in range(cycle_count):
            # Execute instructions as required; each warrior executes one
            for i in range(len(o.process_queue)):
                o.state_data, o.process_queue[i] = execute_process(o.process_queue[i], o.state_data)

                if o.process_queue[i] == []:
                    # Warrior has no remaining processes and is eliminated
                    o.warriors_temp.pop(i)
                    o.process_queue.pop(i)
                    for tile in o.state_data:
                        if tile.warrior != i: continue
                        tile.color = "cross_" + tile.color

        o.update_requested = True
        o.cur_cycle += cycle_count

        if o.cur_cycle >= o.max_cycle_count:
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

    state, process = evaluate_instruction(state, state[process.location].instruction, process)

    # Add the updated process back to the queue unless it has been killed
    if not process.dying:
        queue.append(process)

    return state, queue

def evaluate_instruction(state : list, instruction : o.Instruction, process : o.Process):
    # The main execution function
    location_1 = get_absolute_core_location(instruction.a_mode_1, instruction.address_1, process.location)
    location_2 = get_absolute_core_location(instruction.a_mode_2, instruction.address_2, process.location)

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

            if state[location_2].color != state[process.location].color:
                state[location_2].color = "cross_" + state[process.location].color.removeprefix("cross_")

        case "DAT":
            # Kills the current process
            process.dying = True
            return state, process

        case "ADD":
            # Adds the number in the source to the address in the destination
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
            if state[location_1].instruction.address_1 == 0:
                process.dying = True
                return state, process

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

        case "MOD":
            # Performs modulo operation using the target and the source
            if state[location_1].instruction.address_1 == 0:
                process.dying = True
                return state, process

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

        case "JMP":
            # Jumps to the A-field address
            process.location = location_1
            return state, process
        
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
                case "F" | "I" | "X":
                    if state[location_2].instruction.address_1 == 0 and state[location_2].instruction.address_2 == 0:
                        check_passed = True
            if check_passed:
                process.location = location_1
                return state, process

        case "NOP" | "_":
            # No operation
            pass

    # Move the process forward one step
    process.location += 1
    process.location %= o.field_size
        
    return state, process

def get_absolute_core_location(mode : str, value : int, origin : int):
    # Converts an addressing mode-value pair to an absolute value
    next_location = (origin + value) % o.field_size

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
        