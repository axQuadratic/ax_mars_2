# This file stores classes and global variables for easy access
# It also manages the inner workings of the setup and options menus

import customtkinter as ctk

play_speed = 1
field_size = 8000

state_data = ["red_tile" for i in range(20000)]
prev_state_data = []

state_image = None
resized_state_image = None

speed_levels = [1, 2, 3, 4, 5, 10, 25, 50, 75, 100]

def toggle_dark_mode():
    if ctk.get_appearance_mode() == "Light":
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")