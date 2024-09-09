import customtkinter as ctk
import math
from PIL import ImageTk
from ctypes import windll
import graphics
import options as o

# Global variables are declared in options.py

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.geometry("450x220")
root.resizable(False, False)
root.title("axMARS 2.0")

def main():
    global pause_button, speed_display, state_window_button

    # Create UI elements for the main window
    state_window_button = ctk.CTkButton(root, text="View Core", command=open_state_window)

    bottom_container = ctk.CTkFrame(root)
    pause_button = ctk.CTkButton(bottom_container)
    speed_control = ctk.CTkSlider(bottom_container, from_=0, to=9, number_of_steps=9, orientation=ctk.HORIZONTAL, command=change_speed)
    speed_display = ctk.CTkLabel(bottom_container, text="1x", width=35)
    max_speed_button = ctk.CTkCheckBox(bottom_container, text="Enable Asynchronous Rendering")
    pause_button = ctk.CTkButton(bottom_container, text="Start", command=toggle_pause)
    options_button = ctk.CTkButton(bottom_container, text="Options", command=o.toggle_dark_mode)
    help_button = ctk.CTkButton(bottom_container, text="Help", state=ctk.DISABLED)

    state_window_button.grid(row=0, column=0)
    bottom_container.grid(row=2, column=0, sticky="nsew")

    pause_button.grid(row=0, column=0, columnspan=2, sticky="nsew")
    speed_control.grid(row=1, column=0, sticky="ew")
    speed_display.grid(row=1, column=1, sticky="nsew")
    max_speed_button.grid(row=2, column=0, sticky="nsew")
    options_button.grid(row=0, column=3, rowspan=2, sticky="nsew")
    help_button.grid(row=2, column=3, sticky="sew")

    root.grid_rowconfigure([0, 2], weight=1)
    root.grid_rowconfigure(1, weight=3)
    root.grid_columnconfigure(0, weight=1)

    bottom_container.grid_rowconfigure(2, weight=1)
    bottom_container.grid_columnconfigure(2, weight=1)

    speed_control.set(0)

def change_speed(new_speed):

    o.play_speed = o.speed_levels[math.floor(new_speed)]
        
    speed_display.configure(text=f"{o.play_speed}x")

def toggle_pause():
    pass

def open_state_window():
    global state_window, state_canvas, tile_detail, inst_detail, cycle_detail

    state_window_button.configure(state=ctk.DISABLED, text="Core Readout Active")

    state_window = ctk.CTkToplevel(root)
    state_window.resizable(False, False) # Consider making this resizable in the future; right now resizing it would break everything
    state_window.title("Core Readout")
    state_window.protocol("WM_DELETE_WINDOW", close_state_win) # Intercepts a press of the OS close button

    state_window.grid_rowconfigure(0, weight=1)
    state_window.grid_rowconfigure(1, weight=0) # All widgets on this row are forced to their minimum size
    state_window.grid_columnconfigure(0, weight=1)

    state_canvas = ctk.CTkCanvas(state_window, bg="black")
    state_canvas.grid(row=0, column=0, columnspan=2, sticky="nsew")
    state_canvas.bind("<Motion>", track_mouse_pos)
    
    bottom_bar_container = ctk.CTkFrame(state_window, width=0, height=0)
    bottom_bar_container.grid(row=1, column=0, sticky="nsew")

    bottom_bar_container.grid_rowconfigure(0, weight=1)
    bottom_bar_container.grid_columnconfigure([0, 2, 4, 6], weight=10)
    bottom_bar_container.grid_columnconfigure([1, 3], weight=1)
    bottom_bar_container.grid_columnconfigure(5, weight=20)

    tile_detail = ctk.CTkLabel(bottom_bar_container, bg_color="gray39", text="Address #0000")
    tile_detail.grid(row=0, column=0, sticky="nsew")
    inst_detail = ctk.CTkLabel(bottom_bar_container, bg_color="gray39", text="DAT.F #0, #0")
    inst_detail.grid(row=0, column=2, sticky="nsew")
    cycle_detail = ctk.CTkLabel(bottom_bar_container, bg_color="gray39", text="Cycle 0 / 10000")
    cycle_detail.grid(row=0, column=4, sticky="nsew")
    ctk.CTkButton(bottom_bar_container, command=lambda: open_detail_window(0), text="Open Detail Viewer").grid(row=0, column=6, sticky="nsew")

    update_state_canvas()

def update_state_canvas():

    o.state_image = graphics.create_image_from_state_data(o.state_data, o.prev_state_data, o.field_size, o.state_image)
    resized_image = o.state_image.resize((800, round(o.state_image.height * (800 / o.state_image.width))))
    root.display_image = display_image = ImageTk.PhotoImage(resized_image)
    state_canvas.create_image((405, resized_image.height // 2 + 5), image=display_image)

    # The next step breaks if the Windows scaling setting is above 100%, hence that needs to be checked for
    scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100

    # Recalculate window size based on the size of the image; 40px margin for the border and bottom bar
    state_window.geometry(f"{round(810 / scale_factor)}x{round(resized_image.height / scale_factor) + 40}")

def track_mouse_pos(event):
    global target_tile

    # Calculate mouse position in terms of tiles; note that since the grid is shifted by 5 all events must also be
    tile_x = math.floor(((event.x + 5) / o.state_image.width) * 100)
    tile_y = math.floor(((event.y + 5) / o.state_image.width) * 100)
    
    # Clamp X and Y values
    if tile_x <= 1: tile_x = 1
    if tile_x > graphics.max_field_width: tile_x = graphics.max_field_width
    if tile_y <= 1: tile_y = 1
    if tile_y > o.field_size / graphics.max_field_width: tile_y = o.field_size / graphics.max_field_width

    target_tile = ((tile_y - 1) * graphics.max_field_width + tile_x)

    tile_detail.configure(text=f"Address #{target_tile:04}")

def open_detail_window(target):
    detail_window = ctk.CTkToplevel(root)

def close_state_win():
    state_window_button.configure(state=ctk.NORMAL, text="View Core")
    state_window.destroy()

main()
root.mainloop()
