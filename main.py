# The main program file; acts primarily as UI manager

import customtkinter as ctk
from tkinter.messagebox import showinfo
import math
import threading as th
from PIL import ImageTk
from ctypes import windll
from random import randint
from time import sleep
from pyperclip import copy
from copy import deepcopy
import graphics
import options as o
import compiler

# Global variables are declared in options.py

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("dark-blue")

o.root.geometry("450x200")
o.root.resizable(False, False)
o.root.title("axMARS 2.0")

# This needs to be declared here as its existence is required by several functions
state_window = None

render_thread = None

# These are only used by the Redcode editor, but must be global as they need to be tracked between functions
current_warrior = None
current_edit_id = None

def main():
    global state_window_button, setup_button, options_button, speed_display, pause_button

    # Start the background render thread
    render_thread = th.Thread(target=graphics_listener)
    render_thread.start()

    # Create UI elements for the main window
    top_container = ctk.CTkFrame(o.root)
    state_window_button = ctk.CTkButton(top_container, text="No Core Loaded", command=open_state_window, state=ctk.DISABLED)
    pspace_button = ctk.CTkButton(top_container, text="View P-Space [WIP]", state=ctk.DISABLED)
    setup_button = ctk.CTkButton(top_container, text="Setup", command=open_setup_menu)
    help_button = ctk.CTkButton(top_container, text="Help [WIP]", state=ctk.DISABLED)
    options_button = ctk.CTkButton(top_container, text="Options", command=open_options_menu)

    bottom_container = ctk.CTkFrame(o.root)
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

    o.root.grid_rowconfigure([0, 2], weight=1)
    o.root.grid_rowconfigure(1, weight=3)
    o.root.grid_columnconfigure(0, weight=1)

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
    global warrior_list_container

    setup_window = ctk.CTkToplevel(o.root)
    setup_window.title("Match Options")
    setup_window.geometry("500x275")
    setup_window.resizable(False, False)
    setup_window.grab_set()

    o.warriors_temp = deepcopy(o.warriors) # Reset all unsaved warriors

    random_core = ctk.IntVar()

    warrior_container = ctk.CTkFrame(setup_window)
    warrior_label = ctk.CTkLabel(warrior_container, font=("TkDefaultFont", 14), text="Warriors")
    warrior_list_container = ctk.CTkScrollableFrame(warrior_container, width=150, height=200, bg_color="gray39")
    add_warrior_button = ctk.CTkButton(warrior_container, text="Create Warrior", command=lambda: open_redcode_window(None))
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
    apply_button = ctk.CTkButton(setup_window, text="Apply", command=lambda: o.apply_setup(setup_window, error_label, state_window_button, core_size_input.get(), max_cycle_input.get(), max_length_input.get(), random_core.get()))

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

    warrior_container.grid_rowconfigure(list(range(2, 9)), weight=1)

    misc_container.grid_rowconfigure([2, 3, 5], weight=1)

    core_size_input.insert(0, o.field_size)
    max_cycle_input.insert(0, o.max_cycle_count)
    max_length_input.insert(0, o.max_program_length)

    display_warriors()

def display_warriors():
    for child in warrior_list_container.winfo_children():
        child.destroy()

    warrior_var = ctk.IntVar(value=0)
    i = 0
    for warrior in o.warriors_temp:
        display_color = o.get_tile_hex_color(warrior.color)
        if len(warrior.name) > 13:
            display_name = warrior.name[0:13] + "..."
        else:
            display_name = warrior.name
        new_warrior = ctk.CTkRadioButton(warrior_list_container, width=140, height=30, fg_color=display_color, hover_color=display_color, font=("Consolas", 13), text=display_name, variable=warrior_var, value=i)
        new_warrior.grid(row=i, column=0, sticky="nsew")
        i += 1

def open_redcode_window(warrior):
    global current_warrior, current_edit_id, redcode_window, compiled_display, save_button, clip_button

    redcode_window = ctk.CTkToplevel(o.root)
    redcode_window.geometry("800x600")
    redcode_window.resizable(False, False)
    redcode_window.title("axMARS 2.0 Redcode Editor")
    redcode_window.grab_set()

    redcode_input = ctk.CTkTextbox(redcode_window, font=("Consolas", 12), height=580, wrap=ctk.NONE)

    compiled_container = ctk.CTkScrollableFrame(redcode_window)
    compiled_header = ctk.CTkLabel(compiled_container, anchor="w", text="Parsed Redcode:")
    compiled_display = ctk.CTkLabel(compiled_container, font=("Consolas", 14), anchor="w", justify="left", text="No readable lines")

    button_container = ctk.CTkFrame(redcode_window)
    debug_button = ctk.CTkCheckBox(button_container, text="Enable debug output (slow)")
    compile_button = ctk.CTkButton(button_container, command=lambda: compile_warrior(redcode_input.get("1.0", "end-1c").split("\n"), bool(debug_button.get())), text="Compile")
    save_button = ctk.CTkButton(button_container, text="Add to Core", state=ctk.DISABLED, command=add_current_warrior_to_list)
    export_button = ctk.CTkButton(button_container, text="Save as file [WIP]", state=ctk.DISABLED)
    clip_button = ctk.CTkButton(button_container, text="Copy to clipboard", command=lambda: copy(compiled_display.cget("text")), state=ctk.DISABLED)

    redcode_input.grid(row=0, column=0, rowspan=3, sticky="nsew")

    compiled_container.grid(row=0, column=1, sticky="nsew")
    compiled_header.grid(row=0, column=0, sticky="ew")
    compiled_display.grid(row=1, column=0, sticky="nsew")

    button_container.grid(row=2, column=1, sticky="nsew")
    debug_button.grid(row=0, column=0, columnspan=2, sticky="nsew")
    compile_button.grid(row=1, column=0, columnspan=2, sticky="nsew")
    save_button.grid(row=2, column=0, rowspan=2, sticky="nsew")
    export_button.grid(row=2, column=1, sticky="nsew")
    clip_button.grid(row=3, column=1, sticky="nsew")

    redcode_window.grid_columnconfigure(0, weight=2)
    redcode_window.grid_columnconfigure(1, weight=1)
    redcode_window.grid_rowconfigure(0, weight=10)
    redcode_window.grid_rowconfigure([1, 2], weight=1)

    compiled_container.grid_rowconfigure(0, weight=1)
    compiled_container.grid_rowconfigure(1, weight=10)
    compiled_container.grid_columnconfigure(0, weight=1)

    button_container.grid_rowconfigure([1, 2, 3], weight=1)
    button_container.grid_columnconfigure([0, 1], weight=1)

    if warrior is not None:
        # Editing an extant warrior; needs to insert its data
        current_warrior = warrior
        current_edit_id = warrior.id
        redcode_input.insert(0, warrior.raw_data)
        compile_warrior(warrior.raw_data, False)
    else:
        current_warrior = None
        current_edit_id = None

# Creates a warrior from text data entered by user
def compile_warrior(data, debug):
    global current_warrior

    current_warrior, error_list = compiler.compile_load_file(data, debug)
    if error_list != []:
        # Errors are present
        compiled_display.configure(text_color="red", font=("Consolas", 12), text=f"({len(error_list)} errors)\n{'\n'.join(error_list)}")

        save_button.configure(state=ctk.DISABLED)
        clip_button.configure(state=ctk.DISABLED)
        return

    load_text = []
    for line in current_warrior.load_file:
        load_text.append(o.parse_instruction_to_text(line))

    if load_text == []:
        compiled_display.configure(text_color=("black", "white"), text="No readable lines")
        return

    compiled_display.configure(text_color=("black", "white"), font=("Consolas", 14), text="\n".join(load_text))

    save_button.configure(state=ctk.NORMAL)
    clip_button.configure(state=ctk.NORMAL)

    # The current_warrior variable is used in the below function
    current_warrior.id = len(o.warriors_temp)
    current_warrior.color = [v.name for v in o.tile_colors][current_warrior.id % 8] # Loop through every main colour in tile_colors
    current_warrior.raw_data = data

def add_current_warrior_to_list():
    # This function uses global parameters set at compile-time
    if current_edit_id is None:
        o.warriors_temp.append(current_warrior)
    else:
        # If current_edit_id is set, overwrite the warrior of that id
        for i in range(len(o.warriors_temp)):
            if o.warriors_temp[i].id == current_edit_id:
                o.warriors_temp[i] = current_warrior

    display_warriors()
    redcode_window.destroy()

def open_state_window():
    global state_window, state_canvas, detail_button

    state_window_button.configure(state=ctk.DISABLED, text="Core Readout Active")

    state_window = ctk.CTkToplevel(o.root)
    state_window.resizable(False, False) # Consider making this resizable in the future; right now resizing it would break everything
    state_window.title("Core Readout")
    state_window.protocol("WM_DELETE_WINDOW", close_state_win)

    state_canvas = ctk.CTkCanvas(state_window, bg="black")
    
    bottom_bar_container = ctk.CTkFrame(state_window, width=0, height=0)
    detail_button = ctk.CTkButton(bottom_bar_container, command=open_detail_window, text="Open Detail Viewer")

    state_canvas.grid(row=0, column=0, columnspan=2, sticky="nsew")

    bottom_bar_container.grid(row=1, column=0, sticky="nsew")
    detail_button.grid(row=0, column=6, sticky="nsew")

    state_window.grid_rowconfigure(0, weight=1)
    state_window.grid_rowconfigure(1, weight=0) # All widgets on this row are forced to their minimum size
    state_window.grid_columnconfigure(0, weight=1)

    bottom_bar_container.grid_rowconfigure(0, weight=1)
    bottom_bar_container.grid_columnconfigure([0, 2, 4, 6], weight=10)
    bottom_bar_container.grid_columnconfigure([1, 3], weight=1)
    bottom_bar_container.grid_columnconfigure(5, weight=20)

    o.render_queue.append(o.state_data)

def graphics_listener():
    # Always runs in the background; executes the render queue whenever it is non-empty
    while True:
        sleep(0.05) # Delay to prevent excessive CPU usage

        if o.render_queue == []: continue
        update_state_canvas()

def update_state_canvas():
    global state_window

    # Ignore if function is called when the window is not open
    if state_window is None or not state_window.winfo_exists(): return
    # Ignore if function is called while the render queue is empty
    if o.render_queue == []: return
    # If core is unloaded while window is open, close it
    if o.state_data == []: state_window.destroy()

    o.state_image = graphics.create_image_from_state_data(o.state_data, o.prev_state_data, o.field_size, o.state_image)
    o.resized_state_image = o.state_image.resize((800, round(o.state_image.height * (800 / o.state_image.width))))
    o.root.display_image = display_image = ImageTk.PhotoImage(o.resized_state_image)
    state_canvas.create_image((405, o.resized_state_image.height // 2 + 5), image=display_image)

    # The next step breaks if the Windows scaling setting is above 100%, hence that needs to be checked for
    scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100

    # Recalculate window size based on the size of the image; 40px margin for the border and bottom bar
    state_window.geometry(f"{round(810 / scale_factor)}x{round(o.resized_state_image.height / scale_factor) + 40}")

    o.render_queue.pop(0)
        
def close_state_win():
    state_window_button.configure(state=ctk.NORMAL, text="View Core")
    state_window.destroy()

def open_detail_window():
    global detail_window, detail_target, search_value, info_labels

    detail_target = 0

    detail_button.configure(state=ctk.DISABLED, text="Detail Viewer Active")

    detail_window = ctk.CTkToplevel(o.root)
    detail_window.title("Core Details")
    detail_window.geometry("300x300")
    detail_window.resizable(False, False)
    detail_window.protocol("WM_DELETE_WINDOW", close_detail_win)

    search_value = ctk.StringVar()
    search_bar = ctk.CTkEntry(detail_window, textvariable=search_value, placeholder_text="Jump to Address...")
    search_value.trace_add("write", lambda _a, _b, _c: update_detail_window(search_value.get(), True))
    data_container = ctk.CTkFrame(detail_window, fg_color="black")
    options_container = ctk.CTkFrame(detail_window, width=30)

    info_labels = []
    for i in range(10):
        info_labels.append(ctk.CTkLabel(data_container, text_color="white", text=f"#{str(i + 1).zfill(4 if o.field_size < 10000 else 5)}: DAT.F #0, #0"))

    up_ten_button = ctk.CTkButton(options_container, text="-10", width=30, command=lambda: update_detail_window(detail_target - 10, False))
    up_one_button = ctk.CTkButton(options_container, text="↑", width=30, command=lambda: update_detail_window(detail_target - 1, False))
    down_one_button = ctk.CTkButton(options_container, text="↓", width=30, command=lambda: update_detail_window(detail_target + 1, False))
    down_ten_button = ctk.CTkButton(options_container, text="+10", width=30, command=lambda: update_detail_window(detail_target + 10, False))

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

    update_detail_window(detail_target, False)

def update_detail_window(target, from_search):
    global detail_target, info_labels, search_value

    if not from_search:
        search_value.set("")

    if type(target) != int:
        # Target value comes from search bar
        try: target = int(target) - 1
        except: return

    if target < 0:
        update_detail_window(0, from_search)
        return
    if target > o.field_size - 10:
        update_detail_window(o.field_size - 10, from_search)
        return

    for i in range(len(o.state_data)):
        o.state_data[i].highlighted = False

    detail_target = target
    for i in range(len(info_labels)):
        info_labels[i].configure(text=f"#{str(detail_target + i + 1).zfill(4 if o.field_size < 10000 else 5)}: {o.parse_instruction_to_text(o.state_data[detail_target + i].instruction)}")
        info_labels[i].configure(text_color=o.get_tile_hex_color(o.state_data[detail_target + i].color) if o.state_data[detail_target + i].color != "black" else "white")
        info_labels[i].configure(font=("Consolas", 15))
        o.state_data[detail_target + i].highlighted = True

    o.render_queue.append(o.state_data)

def close_detail_win():
    for i in range(len(o.state_data)):
        o.state_data[i].highlighted = False
    o.render_queue = [o.state_data]
    try: detail_button.configure(state=ctk.NORMAL, text="Open Detail Viewer")
    except: pass
    detail_window.destroy()

def open_options_menu():
    options_window = ctk.CTkToplevel(o.root)
    options_window.geometry("250x200")
    options_window.resizable(False, False)
    options_window.title("Program Options")
    options_window.grab_set()

    credits_text = "axMARS 2.0\n\nDeveloped by Nils K (Quadratic) for Indirect UF\n\nInspired by pMARS, CoreWin and the defunct corewar.io\n\nLibraries used: customtkinter, PIL, pyperclip & dependencies\n\nProbably dedicated to someone, IDK"

    dark_mode_toggle = ctk.CTkCheckBox(options_window, command=o.toggle_dark_mode, text="Dark Mode")
    credits_button = ctk.CTkButton(options_window, command=lambda: showinfo(title="Credits", message=credits_text), text="Credits")

    dark_mode_toggle.grid(row=0, column=0, sticky="nsew")
    credits_button.grid(row=1, column=0, sticky="ns")

    options_window.grid_columnconfigure(0, weight=1)

    # Set options as needed
    if ctk.get_appearance_mode() == "Dark": dark_mode_toggle.select()

main()
o.root.mainloop()
