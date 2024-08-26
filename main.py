import customtkinter as ctk
from PIL import Image, ImageTk
import graphics

# Global variables are declared here
play_speed = 0
field_size = 8000
state_data = ["red_tile" for i in range(8000)]
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
    global state_window, state_canvas

    state_window_button.configure(state=ctk.DISABLED, text="Core Readout Active")

    state_window = ctk.CTkToplevel(root)
    state_window.geometry("800x820")
    #state_window.resizable(False, False) # Consider making this resizable in the future; right now resizing it would break everything
    state_window.title("Core Readout")
    state_window.protocol("WM_DELETE_WINDOW", close_state_win) # Intercepts a press of the OS close button

    # 40:1 = 800:20
    state_window.grid_rowconfigure(0, weight=40)
    state_window.grid_rowconfigure(1, weight=1)
    state_window.grid_columnconfigure(0, weight=1)

    state_canvas = ctk.CTkCanvas(state_window, bg="black")
    state_canvas.grid(row=0, column=0, columnspan=2, sticky="nsew")
    bottom_bar_container = ctk.CTkFrame(state_window, width=0, height=0)
    bottom_bar_container.grid(row=1, column=0, sticky="nsew")

    bottom_bar_container.grid_rowconfigure(0, weight=1)
    bottom_bar_container.grid_columnconfigure([0, 2, 4, 6], weight=10)
    bottom_bar_container.grid_columnconfigure([1, 3], weight=1)
    bottom_bar_container.grid_columnconfigure(5, weight=20)

    tile_detail = ctk.CTkLabel(bottom_bar_container, bg_color="gray", text="Address #XXXX")
    tile_detail.grid(row=0, column=0, sticky="nsew")
    write_detail = ctk.CTkLabel(bottom_bar_container, bg_color="gray", text="DAT.F #0, #0")
    write_detail.grid(row=0, column=2, sticky="nsew")
    tile_detail = ctk.CTkLabel(bottom_bar_container, bg_color="gray", text="Last read by:\nNone")
    tile_detail.grid(row=0, column=4, sticky="nsew")
    ctk.CTkButton(bottom_bar_container, text="Open Detail Viewer").grid(row=0, column=6, sticky="nsew")

    update_state_canvas()

def update_state_canvas():
    global state_image

    state_image = graphics.create_image_from_state_data(state_data, prev_state_data, field_size, state_image)
    root.display_image = display_image = ImageTk.PhotoImage(state_image)
    state_canvas.create_image(50, 10, image=display_image)

def close_state_win():
    state_window_button.configure(state=ctk.NORMAL, text="View Core")
    state_window.destroy()

main()
root.mainloop()
