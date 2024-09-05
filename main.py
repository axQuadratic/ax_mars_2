import customtkinter as ctk
import math
from PIL import Image, ImageTk
from ctypes import windll
import graphics

# Global variables are declared here
play_speed = 0
field_size = 8000
state_data = ["red_tile" for i in range(20000)]
prev_state_data = []
state_image = None

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.geometry("400x220")
root.resizable(False, False)
root.title("axMARS 2.0")

def main():
    global pause_button, speed_control, state_window_button

    # Create UI elements for the main window
    pause_button = ctk.CTkButton(root)
    speed_control = ctk.CTkSlider(root, from_=0, to=10, orientation=ctk.HORIZONTAL)
    state_window_button = ctk.CTkButton(root, text="View Core", command=open_state_window)

    state_window_button.pack(anchor=ctk.CENTER)

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

    tile_detail = ctk.CTkLabel(bottom_bar_container, bg_color="gray", text="Address #0000")
    tile_detail.grid(row=0, column=0, sticky="nsew")
    inst_detail = ctk.CTkLabel(bottom_bar_container, bg_color="gray", text="DAT.F #0, #0")
    inst_detail.grid(row=0, column=2, sticky="nsew")
    cycle_detail = ctk.CTkLabel(bottom_bar_container, bg_color="gray", text="Cycle 0 / 10000")
    cycle_detail.grid(row=0, column=4, sticky="nsew")
    ctk.CTkButton(bottom_bar_container, command=open_detail_window, text="Open Detail Viewer").grid(row=0, column=6, sticky="nsew")

    update_state_canvas()

def update_state_canvas():
    global state_image

    state_image = graphics.create_image_from_state_data(state_data, prev_state_data, field_size, state_image)
    state_image = state_image.resize((800, round(state_image.height * (800 / state_image.width))))
    root.display_image = display_image = ImageTk.PhotoImage(state_image)
    state_canvas.create_image((405, state_image.height // 2 + 5), image=display_image)

    # The next step breaks if the Windows scaling setting is above 100%, hence that needs to be checked for
    scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100

    # Recalculate window size based on the size of the image; 40px margin for the border and bottom bar
    state_window.geometry(f"{round(810 / scale_factor)}x{round(state_image.height / scale_factor) + 40}")

def track_mouse_pos(event):
    # Calculate mouse position in terms of tiles; note that since the grid is shifted by 5 all events must also be
    tile_x = math.floor(((event.x + 5) / state_image.width) * 100)
    tile_y = math.floor(((event.y + 5) / state_image.width) * 100)
    
    # Clamp X and Y values
    if tile_x <= 1: tile_x = 1
    if tile_x > graphics.max_field_width: tile_x = graphics.max_field_width
    if tile_y <= 1: tile_y = 1
    if tile_y > field_size / graphics.max_field_width: tile_y = field_size / graphics.max_field_width

    #tile = 

    tile_detail.configure(text=f"Address #{((tile_y - 1) * graphics.max_field_width + tile_x):04}")

def open_detail_window():
    pass

def close_state_win():
    state_window_button.configure(state=ctk.NORMAL, text="View Core")
    state_window.destroy()

main()
root.mainloop()
