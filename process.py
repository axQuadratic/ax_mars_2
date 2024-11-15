# This file handles the underlying simulation part of the program

import options as o
from time import sleep
import math

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
            elif o.play_speed < 5:
                sleep(1 / o.play_speed)
            else:
                # Above 5x speed, multiple instructions are run at once to decrease rendering demand
                cycle_count = math.ceil(o.play_speed / 5)
                sleep(0.2)
            if o.paused or o.sim_completed: continue

        if o.cur_cycle + cycle_count > o.max_cycle_count:
            cycle_count = o.max_cycle_count - o.cur_cycle

        # Reset all read highlights in state data
        for i in range(len(o.state_data)):
            o.state_data[i].read_marked = False

        for i in range(cycle_count):
            # Execute instructions as required
            current_process = o.process_queue.pop(0)
            o.state_data = execute_instruction(current_process, o.state_data)

        o.update_requested = True
        o.cur_cycle += cycle_count

        if o.cur_cycle >= o.max_cycle_count:
            # End the simulation
            print("Simulation complete.")
            o.sim_completed = True

        if single_step:
            # Advance button only executes one cycle
            break

def execute_instruction(process : o.Process, state : list):
    # The main execution function

    # Apply read marker to the currently targeted instruction
    state[process.location].color = o.get_tile_color_from_id(process.warrior)

    # Move the process forward one step
    process.location += 1
    process.location %= o.field_size
    o.process_queue.append(process)

    # Add read highlight to new process location unless max speed is enabled
    if not o.max_speed_enabled: state[process.location].read_marked = True
    return state