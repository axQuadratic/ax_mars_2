# The main program file; acts primarily as UI manager

import customtkinter as ctk
from tkinter.messagebox import showinfo
import math
import threading as th
from PIL import ImageTk
from ctypes import windll
from random import randint
from time import sleep
import graphics
import options as o

# Global variables are declared in options.py

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.geometry("450x200")
root.resizable(False, False)
root.title("axMARS 2.0")

render_thread = None

def main():
    global state_window_button, setup_button, options_button, speed_display, pause_button

    # Start the background render thread
    render_thread = th.Thread(target=graphics_listener)
    render_thread.start()

    # Create UI elements for the main window
    top_container = ctk.CTkFrame(root)
    state_window_button = ctk.CTkButton(top_container, text="View Core", command=open_state_window)
    pspace_button = ctk.CTkButton(top_container, text="View P-Space [WIP]", state=ctk.DISABLED)
    setup_button = ctk.CTkButton(top_container, text="Setup", command=open_setup_menu)
    help_button = ctk.CTkButton(top_container, text="Help [WIP]", state=ctk.DISABLED)
    options_button = ctk.CTkButton(top_container, text="Options", command=open_options_menu)

    bottom_container = ctk.CTkFrame(root)
    speed_control = ctk.CTkSlider(bottom_container, from_=0, to=9, number_of_steps=9, orientation=ctk.HORIZONTAL, command=change_speed)
    speed_display = ctk.CTkLabel(bottom_container, text="1x", width=35)
    max_speed_button = ctk.CTkCheckBox(bottom_container, text="Max. Simulation Speed")
    async_button = ctk.CTkCheckBox(bottom_container, text="Asynchronous Rendering")
    pause_button = ctk.CTkButton(bottom_container, text="Start", command=toggle_pause)
    one_step_button = ctk.CTkButton(bottom_container, text="Advance One Cycle")

    top_container.grid(row=0, column=0, sticky="nsew")
    bottom_container.grid(row=2, column=0, sticky="nsew")

    state_window_button.grid(row=0, column=0, sticky="nsew")
    pspace_button.grid(row=2, column=0, sticky="nsew")
    setup_button.grid(row=0, column=2, rowspan=3, sticky="nsew")
    help_button.grid(row=0, column=4, sticky="nsew")
    options_button.grid(row=2, column=4, sticky="nsew")

    pause_button.grid(row=0, column=0, columnspan=2, sticky="nsew")
    speed_control.grid(row=1, column=0, sticky="ew")
    speed_display.grid(row=1, column=1, sticky="nsew")
    max_speed_button.grid(row=2, column=0, sticky="nsew")
    async_button.grid(row=2, column=2, columnspan=2, sticky="nsew")
    one_step_button.grid(row=0, column=3, sticky="nsew")

    root.grid_rowconfigure([0, 2], weight=1)
    root.grid_rowconfigure(1, weight=3)
    root.grid_columnconfigure(0, weight=1)

    top_container.grid_rowconfigure(1, weight=1)
    top_container.grid_columnconfigure([1, 3], weight=1)

    bottom_container.grid_rowconfigure(2, weight=1)
    bottom_container.grid_columnconfigure(2, weight=1)

    speed_control.set(0)

def change_speed(new_speed):
    o.play_speed = o.speed_levels[math.floor(new_speed)]
        
    speed_display.configure(text=f"{o.play_speed}x")

def toggle_pause():
    pass

def open_setup_menu():

    setup_window = ctk.CTkToplevel(root)
    setup_window.title("Match Options")
    setup_window.geometry("500x275")
    setup_window.resizable(False, False)
    setup_window.grab_set()

    random_core = ctk.IntVar()

    warrior_container = ctk.CTkFrame(setup_window)
    warrior_label = ctk.CTkLabel(warrior_container, font=("TkDefaultFont", 14), text="Warriors")
    warrior_list_container = ctk.CTkScrollableFrame(warrior_container, width=150, height=200, bg_color="gray39")
    add_warrior_button = ctk.CTkButton(warrior_container, text="Create Warrior")
    import_warrior_button = ctk.CTkButton(warrior_container, text="Import Load File [WIP]", state=ctk.DISABLED)
    edit_warrior_button = ctk.CTkButton(warrior_container, text="Edit Selected", state=ctk.DISABLED)
    remove_warrior_button = ctk.CTkButton(warrior_container, text="Remove Selected", state=ctk.DISABLED)

    core_size_container = ctk.CTkFrame(setup_window)
    core_size_label = ctk.CTkLabel(core_size_container, font=("TkDefaultFont", 14), text="Core Size")
    core_size_input = ctk.CTkEntry(core_size_container, placeholder_text="Size...")
    random_button = ctk.CTkCheckBox(core_size_container, text="Random", command=lambda: core_size_input.configure(state=ctk.DISABLED if random_button.get() == 1 else ctk.NORMAL), variable=random_core)

    misc_container = ctk.CTkFrame(setup_window)
    misc_label = ctk.CTkLabel(misc_container, font=("TkDefaultFont", 14), text="Miscellaneous")
    max_cycle_label = ctk.CTkLabel(misc_container, text="Max. Cycles:")
    max_cycle_input = ctk.CTkEntry(misc_container, placeholder_text="Cycles...")
    max_length_label = ctk.CTkLabel(misc_container, text="Max. Program Length:")
    max_length_input = ctk.CTkEntry(misc_container, placeholder_text="Length...")

    error_label = ctk.CTkLabel(setup_window, text_color="red", text="")
    apply_button = ctk.CTkButton(setup_window, text="Apply", command=lambda: apply_setup(setup_window, error_label, core_size_input.get(), max_cycle_input.get(), max_length_input.get(), random_core.get()))

    warrior_container.grid(row=0, column=0, rowspan=2, sticky="nsew")
    core_size_container.grid(row=0, column=2, sticky="new")
    misc_container.grid(row=1, column=2, sticky="sw")

    warrior_label.grid(row=1, column=1, columnspan=2, sticky="nsew")
    warrior_list_container.grid(row=2, column=1, rowspan=8, sticky="nsew")
    add_warrior_button.grid(row=2, column=2, sticky="nsew")
    import_warrior_button.grid(row=4, column=2, sticky="nsew")
    edit_warrior_button.grid(row=6, column=2, sticky="nsew")
    remove_warrior_button.grid(row=8, column=2, sticky="nsew")

    core_size_label.grid(row=0, column=0, sticky="nsew")
    core_size_input.grid(row=1, column=0, sticky="nsew")
    random_button.grid(row=2, column=0, sticky="nsew")

    misc_label.grid(row=0, column=0, columnspan=2, sticky="nsew")
    max_cycle_label.grid(row=1, column=0, sticky="nsew")
    max_cycle_input.grid(row=2, column=0, sticky="nsew")
    max_length_label.grid(row=4, column=0, sticky="nsew")
    max_length_input.grid(row=5, column=0, sticky="nsew")

    error_label.grid(row=2, column=0, columnspan=3, sticky="nsew")
    apply_button.grid(row=3, column=0, columnspan=3, sticky="sew")

    setup_window.grid_rowconfigure([0, 1, 2], weight=1)
    setup_window.grid_columnconfigure(1, weight=1)

    warrior_container.grid_rowconfigure([2, 3, 4, 5, 6, 7, 8], weight=1)

    misc_container.grid_rowconfigure([2, 3, 5], weight=1)

    core_size_input.insert(0, o.field_size)
    max_cycle_input.insert(0, o.max_cycle_count)
    max_length_input.insert(0, o.max_program_length)

def apply_setup(window, label, core_size, max_cycles, max_length, random_core):
    # Error checking
    try:
        if random_core == 1:
            core_size = randint(max_length * len(o.warriors), 20000)

        core_size = int(core_size)
        max_cycles = int(max_cycles)
        max_length = int(max_length)

        if max_cycles <= 0 or max_length <= 0:
            raise Exception
    except:
        label.configure(text="One or more parameters has an invalid value")
        return
    
    if core_size < max_length * len(o.warriors):
        label.configure(text="Core size cannot be smaller than max. warrior length * warrior count")
        return
    
    o.field_size = core_size
    o.max_cycle_count = max_cycles
    o.max_program_length = max_length
    
    window.destroy()
    graphics.render_queue.append(o.state_data) # The core viewer, if it is open, needs to be updated

def open_state_window():
    global state_window, state_canvas, detail_button

    state_window_button.configure(state=ctk.DISABLED, text="Core Readout Active")

    state_window = ctk.CTkToplevel(root)
    state_window.resizable(False, False) # Consider making this resizable in the future; right now resizing it would break everything
    state_window.title("Core Readout")
    state_window.protocol("WM_DELETE_WINDOW", close_state_win)

    state_canvas = ctk.CTkCanvas(state_window, bg="black")

    #state_canvas.bind("<Motion>", track_mouse_pos)
    
    bottom_bar_container = ctk.CTkFrame(state_window, width=0, height=0)
    #tile_detail = ctk.CTkLabel(bottom_bar_container, bg_color="gray39", text=f"Address #{'0000' if o.field_size < 10000 else '00000'}")
    #inst_detail = ctk.CTkLabel(bottom_bar_container, bg_color="gray39", text="DAT.F #0, #0")
    #cycle_detail = ctk.CTkLabel(bottom_bar_container, bg_color="gray39", text="Cycle 0 / 10000")
    detail_button = ctk.CTkButton(bottom_bar_container, command=open_detail_window, text="Open Detail Viewer")

    state_canvas.grid(row=0, column=0, columnspan=2, sticky="nsew")

    bottom_bar_container.grid(row=1, column=0, sticky="nsew")
    #tile_detail.grid(row=0, column=0, sticky="nsew")
    #inst_detail.grid(row=0, column=2, sticky="nsew")
    #cycle_detail.grid(row=0, column=4, sticky="nsew")
    detail_button.grid(row=0, column=6, sticky="nsew")

    state_window.grid_rowconfigure(0, weight=1)
    state_window.grid_rowconfigure(1, weight=0) # All widgets on this row are forced to their minimum size
    state_window.grid_columnconfigure(0, weight=1)

    bottom_bar_container.grid_rowconfigure(0, weight=1)
    bottom_bar_container.grid_columnconfigure([0, 2, 4, 6], weight=10)
    bottom_bar_container.grid_columnconfigure([1, 3], weight=1)
    bottom_bar_container.grid_columnconfigure(5, weight=20)

    graphics.render_queue.append(o.state_data)

def graphics_listener():
    # Always runs in the background; executes the render queue whenever it is non-empty
    while True:
        sleep(0.1) # Delay to prevent excessive CPU usage
        if graphics.render_queue == []: continue
        update_state_canvas()

def update_state_canvas():
    global state_window

    # Ignore if function is called when the window is not open
    if state_window is None or not state_window.winfo_exists(): return
    # Ignore if function is called while the render queue is empty
    if graphics.render_queue == []: return

    o.state_image = graphics.create_image_from_state_data(o.state_data, o.prev_state_data, o.field_size, o.state_image)
    o.resized_state_image = o.state_image.resize((800, round(o.state_image.height * (800 / o.state_image.width))))
    root.display_image = display_image = ImageTk.PhotoImage(o.resized_state_image)
    state_canvas.create_image((405, o.resized_state_image.height // 2 + 5), image=display_image)

    # The next step breaks if the Windows scaling setting is above 100%, hence that needs to be checked for
    scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100

    # Recalculate window size based on the size of the image; 40px margin for the border and bottom bar
    state_window.geometry(f"{round(810 / scale_factor)}x{round(o.resized_state_image.height / scale_factor) + 40}")

    graphics.render_queue.pop(0)

# The below code is currently nonfunctional: I have decided to comment it out until I can be bothered to fix it
"""
def track_mouse_pos(event):
    # Recalculate the width in tiles of the field using the same algorithm as the graphics manager
    e_field_width = graphics.max_field_width if o.field_size <= 10000 else math.ceil(math.sqrt(o.field_size))

    # Calculate mouse position in terms of tiles; note that since the grid is shifted by 5 all events must also be
    tile_x = math.floor(((event.x + 5) / o.resized_state_image.width) * e_field_width)
    tile_y = math.floor(((event.y + 5) / o.resized_state_image.width) * e_field_width)

    # Clamp X and Y values
    if tile_x <= 1: tile_x = 1
    if tile_x > e_field_width: tile_x = e_field_width
    if tile_y <= 1: tile_y = 1
    if tile_y > o.field_size / e_field_width: tile_y = o.field_size / e_field_width

    target_tile = ((tile_y - 1) * e_field_width + tile_x)
    if target_tile > o.field_size: target_tile = o.field_size

    if o.field_size >= 10000:
        tile_detail.configure(text=f"Address #{target_tile:05}")
    else:
        tile_detail.configure(text=f"Address #{target_tile:04}")
"""
        
def close_state_win():
    state_window_button.configure(state=ctk.NORMAL, text="View Core")
    state_window.destroy()

def open_detail_window():
    global detail_window, detail_target, search_value, info_labels

    detail_target = 0

    detail_button.configure(state=ctk.DISABLED, text="Detail Viewer Active")

    detail_window = ctk.CTkToplevel(root)
    detail_window.title("Core Details")
    detail_window.geometry("300x300")
    detail_window.resizable(False, False)
    detail_window.protocol("WM_DELETE_WINDOW", close_detail_win)

    search_value = ctk.StringVar()
    search_bar = ctk.CTkEntry(detail_window, textvariable=search_value, placeholder_text="Jump to Address...")
    search_value.trace_add("write", detail_search)
    data_container = ctk.CTkFrame(detail_window, fg_color="black")
    options_container = ctk.CTkFrame(detail_window, width=30)

    info_labels = []
    for i in range(10):
        info_labels.append(ctk.CTkLabel(data_container, text_color="white", text=f"#{str(i + 1).zfill(4 if o.field_size < 10000 else 5)}: DAT.F #0, #0"))

    up_ten_button = ctk.CTkButton(options_container, text="-10", width=30, command=lambda: update_detail_window(detail_target - 10))
    up_one_button = ctk.CTkButton(options_container, text="↑", width=30, command=lambda: update_detail_window(detail_target - 1))
    down_one_button = ctk.CTkButton(options_container, text="↓", width=30, command=lambda: update_detail_window(detail_target + 1))
    down_ten_button = ctk.CTkButton(options_container, text="+10", width=30, command=lambda: update_detail_window(detail_target + 10))

    search_bar.grid(row=0, column=0, columnspan=2, sticky="nsew")
    data_container.grid(row=1, column=0, sticky="nsew")
    options_container.grid(row=1, column=1, sticky="ns")

    for i in range(len(info_labels)):
        info_labels[i].grid(row=i, column=0, sticky="nsew")

    up_ten_button.grid(row=0, column=0, sticky="nsew")
    up_one_button.grid(row=1, column=0, sticky="nsew")
    down_one_button.grid(row=2, column=0, sticky="nsew")
    down_ten_button.grid(row=3, column=0, sticky="nsew")

    detail_window.grid_rowconfigure(1, weight=1)
    detail_window.grid_columnconfigure(0, weight=1)

    data_container.grid_rowconfigure(list(range(len(info_labels) + 1)), weight=1)

    options_container.grid_rowconfigure([0, 1, 2, 3], weight=1)
    options_container.grid_rowconfigure(0, weight=1)

    update_detail_window(detail_target)

def update_detail_window(target):
    global detail_target, info_labels

    if type(target) != int:
        # Target value comes from search bar
        try: target = int(target) - 1
        except: return

    if target < 0:
        update_detail_window(0)
        return
    if target > o.field_size - 10:
        update_detail_window(o.field_size - 10)
        return

    for i in range(len(o.state_data)):
        o.state_data[i].highlighted = False

    detail_target = target
    for i in range(len(info_labels)):
        info_labels[i].configure(text=f"#{str(detail_target + i + 1).zfill(4 if o.field_size < 10000 else 5)}: {o.state_data[detail_target + i].instruction}")
        info_labels[i].configure(text_color=graphics.tile_colors(o.state_data[detail_target + i].color) if o.state_data[detail_target + i].color != "black" and o.state_data[detail_target + i].color != "highlight" else "white")
        o.state_data[detail_target + i].highlighted = True

    graphics.render_queue.append(o.state_data)

# Wrapper callback for the search bar trace
def detail_search(a, b, c):
    global search_value
    update_detail_window(search_value.get())

def close_detail_win():
    for i in range(len(o.state_data)):
        o.state_data[i].highlighted = False
    graphics.render_queue = [o.state_data]
    try: detail_button.configure(state=ctk.NORMAL, text="Open Detail Viewer")
    except: pass
    detail_window.destroy()

def open_options_menu():
    options_window = ctk.CTkToplevel(root)
    options_window.geometry("250x200")
    options_window.resizable(False, False)
    options_window.title("Program Options")
    options_window.grab_set()

    credits_text = "axMARS 2.0\n\nDeveloped by Nils K (Quadratic) for Indirect UF\n\nInspired by pMARS, CoreWin and the defunct corewar.io\n\nLibraries used: customtkinter, PIL, ctypes & dependencies\n\nProbably dedicated to someone, IDK"

    dark_mode_toggle = ctk.CTkCheckBox(options_window, command=o.toggle_dark_mode, text="Dark Mode")
    credits_button = ctk.CTkButton(options_window, command=lambda: showinfo(title="Credits", message=credits_text), text="Credits")

    dark_mode_toggle.grid(row=0, column=0, sticky="nsew")
    credits_button.grid(row=1, column=0, sticky="ns")

    options_window.grid_columnconfigure(0, weight=1)

    # Set options as needed
    if ctk.get_appearance_mode() == "Dark": dark_mode_toggle.select()

main()
root.mainloop()
