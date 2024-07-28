import tkinter as tk
from PIL import Image, ImageTk
import random as r
import datetime as dt
import math
import os

import objects as o

displayed_image = None
canvas = None
pil_image = None

tile_colors = []
prev_tile_colors = []

side = 0

root = tk.Tk()

runs = 0

def main():
    entry = tk.Entry(root)
    entry.pack(anchor=tk.N)
    tk.Button(root, text="Run Benchmark", command=lambda: update_tile_field(int(entry.get()))).pack(anchor=tk.CENTER)
    root.mainloop()

def update_tile_field(tile_count : int):
    global displayed_image, canvas, runs, pil_image, tile_colors, prev_tile_colors, side

    runs += 1
    start_time = dt.datetime.now().timestamp()
    side = math.ceil(math.sqrt(tile_count))

    if pil_image is None:
        pil_image = Image.new("RGB", (side * o.tile_size, side * o.tile_size), (0, 0, 0))
    pixel = pil_image.load()

    if tile_colors == [] :
        prev_tile_colors = [None for i in range(tile_count)]
        for i in range(tile_count):
            tile_colors.append(r.choice(list(o.tiles.keys())))
    else:
        for i in range(12):
            tile_colors[r.randint(0, len(tile_colors) - 1)] = r.choice(list(o.tiles.keys()))

    sim_tile_count = 0
    updated_tile_count = 0
    for y in range(side):
        for x in range(side):
            if tile_colors[sim_tile_count] != prev_tile_colors[sim_tile_count]:
                pixel = place_tile(pixel, x * o.tile_size, y * o.tile_size, tile_colors[sim_tile_count])
                updated_tile_count += 1
            sim_tile_count += 1

            if sim_tile_count >= tile_count:
                break
        if sim_tile_count >= tile_count:
            break
    
    prev_tile_colors = tile_colors[:]

    res_image = pil_image.resize((pil_image.width // 3, pil_image.height // 3))
    displayed_image = ImageTk.PhotoImage(res_image)
    if canvas is not None:
        canvas.destroy()
    canvas = tk.Canvas(root, width=res_image.width, height=res_image.height, bg="black")
    canvas.pack(anchor=tk.CENTER)
    canvas.create_image(2, 2, anchor=tk.NW, image=displayed_image)
    canvas.bind("<1>", open_detail_window)
    root.update()

    elapsed_time = dt.datetime.now().timestamp() - start_time
    os.system("cls")
    print(f"Simulation complete.\nSimulated tiles: {tile_count} ({updated_tile_count} updated)\nElapsed time: {elapsed_time} seconds\nCurrent runs: {runs}")
    
    update_tile_field(tile_count)

def place_tile(data, x : int, y : int, color : str):
    for i in range(o.tile_size):
        for j in range(o.tile_size):
            data[j + x, i + y] = o.tiles[color][o.tile_size * i + j]

    return data

def open_detail_window(event):
    tile_x = math.ceil(event.x / o.tile_size * (pil_image.width / canvas.winfo_width()))
    tile_y = math.ceil(event.y / o.tile_size * (pil_image.height / canvas.winfo_height()))
    print(f"Click at {event.x}, {event.y}\nViewing tile {tile_x}, {tile_y} (index {side * (tile_y - 1) + tile_x})")

main()
