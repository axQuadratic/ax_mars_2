# This file handles the underlying simulation part of the program

import options as o
from time import sleep

def simulation_clock():
    # Executes every interval given by play speed; triggers match turn calculations
    while True:
        sleep(1 / o.play_speed)
        if o.paused: continue

        current_process = o.process_queue.pop(0)
        o.state_data = execute_instruction(current_process, o.state_data)

        o.render_queue = [True]
        o.cur_cycle += 1

def execute_instruction(process : o.Process, state : list):
    # The main execution function
    print(f"Executing instruction at #{process.location} (warrior ID: {process.warrior})")

    o.process_queue.append(process)
    return state