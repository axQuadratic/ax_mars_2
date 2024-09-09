import customtkinter as ctk

# This file stores classes and global variables for easy access
# It also manages the inner workings of the options menu

play_speed = 1
speed_levels = [1, 2, 3, 4, 5, 10, 25, 50, 75, 100]
field_size = 8000
state_data = ["red_tile" for i in range(20000)]
prev_state_data = []
state_image = None

def toggle_dark_mode():
    if ctk.get_appearance_mode() == "Light":
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")