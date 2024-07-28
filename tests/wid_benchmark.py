import tkinter as tk
import random as r
import datetime as dt
import math
import os

import objects as o
root = tk.Tk()

runs = 0

def main():
    entry = tk.Entry(root)
    entry.pack(anchor=tk.N)
    tk.Button(root, text="Run Benchmark", command=lambda: update_tile_field(int(entry.get()))).pack(anchor=tk.CENTER)
    root.mainloop()

def update_tile_field(tile_count : int):
    global runs
    
    runs += 1
    start_time = dt.datetime.now().timestamp()
    side = math.ceil(math.sqrt(tile_count))

    sim_tile_count = 0
    cur_x = 0
    cur_y = 0

    for i in range(tile_count):
        tk.Frame(bg="red", width=1, height=1).place(x=cur_x, y=cur_y + 50)
        cur_x += 10
        if cur_x > side:
            cur_y += 10
            cur_x = 0

    root.update()

    elapsed_time = dt.datetime.now().timestamp() - start_time
    print(f"Simulation complete.\nSimulated tiles: {tile_count}\nElapsed time: {elapsed_time} seconds\nCurrent runs: {runs}")
    
    #update_tile_field(tile_count)

def draw_tile(data, x : int, y : int, color : str):
    for i in range(o.tile_size):
        for j in range(o.tile_size):
            data[j + x, i + y] = o.tiles[color][j * i]

    return data

main()
