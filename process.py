# This file handles the underlying simulation part of the program

import options as o
from time import sleep
import math

def simulation_clock():
    # Executes every interval given by play speed; triggers match turn calculations
    while True:
        cycle_count = 1

        if o.max_speed_enabled:
            # Immediately run the entire simulation
            cycle_count = o.max_cycle_count - o.cur_cycle
        elif o.play_speed < 5:
            sleep(1 / o.play_speed)
        else:
            # Above 5x speed, multiple instructions are run at once to decrease rendering demand
            cycle_count = math.ceil(o.play_speed / 5)
            sleep(0.2)
        if o.paused: continue

        if o.cur_cycle + cycle_count > o.max_cycle_count:
            cycle_count = o.max_cycle_count - o.cur_cycle

        for i in range(cycle_count):
            # Execute instructions as required
            current_process = o.process_queue.pop(0)
            o.state_data = execute_instruction(current_process, o.state_data)

        o.render_queue = [True]
        o.cur_cycle += cycle_count

        if o.cur_cycle >= o.max_cycle_count:
            # End the simulation
            break

def execute_instruction(process : o.Process, state : list):
    # The main execution function

    # Move read highlight to new process location
    if process.prev_location is not None:
        state[process.prev_location].color = o.warriors[process.warrior].color
    state[process.location].color = "white"

    # Move the process forward one step
    process.prev_location = process.location
    process.location += 1
    process.location %= o.field_size
    o.process_queue.append(process)
    return state