# The main program file; acts primarily as UI manager

import customtkinter as ctk
from tkinter.messagebox import showinfo
from tkinter.filedialog import asksaveasfilename, askopenfilename
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
import process

# Global variables are declared in options.py

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("assets/highlight.json")

o.root.geometry("450x200")
o.root.resizable(False, False)
o.root.title("Tailwind v0.4")
o.root.iconbitmap("assets/tailwind_icon.ico")

# These need to be declared here as their existence is required by several functions
state_window = None
detail_window = None
core_label = None

sim_thread = None

# These are only used by the Redcode editor, but must be global as they need to be tracked between functions
current_warrior = None
current_edit_id = None
current_selection = ctk.IntVar(value=0)

def main():
    global sim_thread, state_window_button, setup_button, options_button, speed_display, pause_button, one_step_button, core_label

    # Start the background threads; graphics and simulation
    sim_thread = th.Thread(target=process.simulation_clock)
    sim_thread.start()
    render_state()

    # Create UI elements for the main window
    top_container = ctk.CTkFrame(o.root)
    state_window_button = ctk.CTkButton(top_container, text="No Core Loaded", command=open_state_window, state=ctk.DISABLED)
    pspace_button = ctk.CTkButton(top_container, text="View P-Space [WIP]", state=ctk.DISABLED)
    setup_button = ctk.CTkButton(top_container, text="Setup", command=open_setup_menu)
    help_button = ctk.CTkButton(top_container, text="Help [WIP]", state=ctk.DISABLED)
    options_button = ctk.CTkButton(top_container, text="Options", command=open_options_menu)

    bottom_container = ctk.CTkFrame(o.root)
    speed_control = ctk.CTkSlider(bottom_container, from_=0, to=8, number_of_steps=8, orientation=ctk.HORIZONTAL, command=change_speed)
    speed_display = ctk.CTkLabel(bottom_container, text="1x", width=35)
    max_speed_button = ctk.CTkCheckBox(bottom_container, text="Max. Simulation Speed", command=lambda: change_speed("max"))
    pause_button = ctk.CTkButton(bottom_container, text="Start", command=toggle_pause, state=ctk.DISABLED)
    one_step_button = ctk.CTkButton(bottom_container, text="Advance One Cycle", command=lambda: process.simulation_clock(True), state=ctk.DISABLED)

    core_frame = ctk.CTkFrame(bottom_container, fg_color="black")
    core_label = ctk.CTkLabel(core_frame, text="No Core Loaded...", font=("Consolas", 12), anchor="w", justify="left")

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
    one_step_button.grid(row=0, column=3, sticky="nsew")

    core_frame.grid(row=2, column=2, columnspan=2, sticky="nsew")
    core_label.grid(row=0, column=1, sticky="nsew")

    o.root.grid_rowconfigure([0, 2], weight=1)
    o.root.grid_rowconfigure(1, weight=3)
    o.root.grid_columnconfigure(0, weight=1)

    top_container.grid_rowconfigure(1, weight=1)
    top_container.grid_columnconfigure([1, 3], weight=1)

    bottom_container.grid_rowconfigure(2, weight=1)
    bottom_container.grid_columnconfigure(2, weight=1)

    core_frame.grid_rowconfigure(0, weight=1)
    core_frame.grid_columnconfigure(0, weight=1)
    core_frame.grid_columnconfigure(1, weight=10)

    speed_control.set(0)

def render_state():
    # Runs five times per second; executes the render queue and checks for simulation completion
        update_core_label()
        if o.update_requested:
            update_state_canvas()
            
        if o.sim_completed:
            # End the simulation
            if not o.paused: toggle_pause()
            pause_button.configure(text="Simulation Complete", state=ctk.DISABLED)
            one_step_button.configure(state=ctk.DISABLED)
        
        o.root.after(20, render_state)

def change_speed(new_speed):
    if new_speed == "max":
        # Max speed button is checked
        o.max_speed_enabled = not o.max_speed_enabled
        return

    o.play_speed = o.speed_levels[math.floor(new_speed)]
        
    speed_display.configure(text=f"{o.play_speed}x")

def toggle_pause():
    if o.paused:
        pause_button.configure(text="Pause")
        one_step_button.configure(state=ctk.DISABLED)
        o.paused = False
    else:
        pause_button.configure(text="Unpause")
        one_step_button.configure(state=ctk.NORMAL)
        o.paused = True
        o.update_requested = True # Ensure rendering is caught up with state

def open_setup_menu():
    global setup_window, warrior_list_container, edit_warrior_button, remove_warrior_button, error_label

    if not o.paused: toggle_pause()

    setup_window = ctk.CTkToplevel(o.root)
    setup_window.title("Match Options")
    setup_window.geometry("500x275")
    setup_window.resizable(False, False)
    setup_window.after(201, lambda: setup_window.iconbitmap("assets/tailwind_icon.ico")) # Workaround for a silly CTk behaviour which sets the icon only after 200ms
    setup_window.grab_set()

    o.warriors_temp = deepcopy(o.warriors) # Reset all unsaved warriors

    random_core = ctk.IntVar()

    warrior_container = ctk.CTkFrame(setup_window)
    warrior_label = ctk.CTkLabel(warrior_container, font=("TkDefaultFont", 14), text="Warriors")
    warrior_list_container = ctk.CTkScrollableFrame(warrior_container, width=150, height=200, bg_color="gray39")
    add_warrior_button = ctk.CTkButton(warrior_container, text="Create Warrior", command=lambda: open_redcode_window(None))
    import_warrior_button = ctk.CTkButton(warrior_container, text="Import Load File", command=import_load_file)
    edit_warrior_button = ctk.CTkButton(warrior_container, text="Edit Selected", command=lambda: open_redcode_window(o.warriors_temp[current_selection.get()]), state=ctk.DISABLED if o.warriors == [] else ctk.NORMAL)
    remove_warrior_button = ctk.CTkButton(warrior_container, text="Remove Selected", command=lambda: delete_warrior(current_selection.get()), state=ctk.DISABLED)

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
    apply_button = ctk.CTkButton(setup_window, text="Apply", command=lambda: apply_setup(core_size_input.get(), max_cycle_input.get(), max_length_input.get(), random_core.get()))

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

    i = 0
    for warrior in o.warriors_temp:
        display_color = o.get_tile_hex_color(warrior.color)
        if len(warrior.name) > 13:
            display_name = warrior.name[0:13] + "..."
        else:
            display_name = warrior.name
        new_warrior = ctk.CTkRadioButton(warrior_list_container, width=140, height=30, fg_color=display_color, hover_color=display_color, font=("Consolas", 13), text=display_name, variable=current_selection, value=i)
        new_warrior.grid(row=i, column=0, sticky="nsew")
        i += 1

def apply_setup(core_size, max_cycles, max_length, random_core):
    # Applies match settings using inputs

    # Error checking
    try:
        if random_core == 1:
            core_size = randint(max_length * len(o.warriors), 20000)

        core_size = int(core_size)
        max_cycles = int(max_cycles)
        max_length = int(max_length)

        if core_size <= 0 or max_cycles <= 0 or max_length <= 0:
            raise Exception
    except:
        error_label.configure(text="One or more parameters has an invalid value")
        return

    if o.warriors_temp == []:
        error_label.configure(text="Cannot begin a match with no warriors in core")
        return
    
    if core_size < max_length * len(o.warriors_temp):
        error_label.configure(text="Core size cannot be smaller than max. warrior length * warrior count")
        return
    
    # Save/reset data in preparation for match
    o.sim_completed = False
    o.cur_cycle = 0

    o.field_size = core_size
    o.max_cycle_count = max_cycles
    o.max_program_length = max_length

    o.warriors = deepcopy(o.warriors_temp)
    o.initialize_core()

    if detail_window is not None:
        close_detail_win()
    if state_window is not None:
        close_state_win()
    else:
        state_window_button.configure(text="View Core", state=ctk.NORMAL)
    pause_button.configure(text="Start", state=ctk.NORMAL)
    one_step_button.configure(state=ctk.NORMAL)
    setup_window.destroy()

def import_load_file():
    # Loads warrior data stored in a .red file, selected by the user
    load_path = askopenfilename(title="Import Warrior", filetypes=[("Redcode '94 Load File", ".red"), ("All files", "*")])
    
    try:
        with open(load_path) as save_file:
            load_data = []
            for line in save_file.readlines():
                load_data.append(line)
    except:
        if load_path == "":
            # Dismissing the popup returns an empty string; this prevents that error
            return
        else:
            # Some other unknown loading error
            error_text = ""
            error_text += "The selected file could not be imported.\n"
            error_text += "It may contain compiler errors, be corrupt,\n"
            error_text += "or simply not contain a Redcode '94 load file."

            showinfo("Import Error", error_text)
            return

    # readlines() reads all data including newline characters; this should sufficiently get rid of them
    load_data = "".join(load_data)
    load_data = load_data.split("\n")
    
    open_redcode_window(o.Warrior(None, None, None, load_data, None))

def open_redcode_window(warrior):
    global current_warrior, current_edit_id, redcode_window, compiled_display, save_button, export_button, clip_button

    redcode_window = ctk.CTkToplevel(o.root)
    redcode_window.geometry("800x600")
    redcode_window.resizable(False, False)
    redcode_window.title("Tailwind Redcode Editor")
    redcode_window.after(201, lambda: redcode_window.iconbitmap("assets/tailwind_icon.ico"))
    redcode_window.grab_set()

    redcode_input = ctk.CTkTextbox(redcode_window, font=("Consolas", 12), height=580, wrap=ctk.NONE)

    compiled_container = ctk.CTkScrollableFrame(redcode_window)
    compiled_header = ctk.CTkLabel(compiled_container, anchor="w", text="Parsed Redcode:")
    compiled_display = ctk.CTkLabel(compiled_container, font=("Consolas", 14), anchor="w", justify="left", text="No current output")

    button_container = ctk.CTkFrame(redcode_window)
    debug_button = ctk.CTkCheckBox(button_container, text="Enable debug output (slow)")
    compile_button = ctk.CTkButton(button_container, command=lambda: compile_warrior(redcode_input.get("1.0", "end-1c").split("\n"), bool(debug_button.get())), text="Compile")
    save_button = ctk.CTkButton(button_container, text="Add to Core", state=ctk.DISABLED, command=add_current_warrior_to_list)
    export_button = ctk.CTkButton(button_container, text="Save as File", command=save_warrior_as_load_file, state=ctk.DISABLED)
    clip_button = ctk.CTkButton(button_container, text="Copy to Clipboard", command=lambda: copy(compiled_display.cget("text")), state=ctk.DISABLED)

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
        try:
            # Editing an extant warrior; needs to insert its data
            current_warrior = warrior
            current_edit_id = warrior.id
            redcode_input.insert("1.0", "\n".join(warrior.raw_data))

            # Precompile the aforementioned warrior
            compile_warrior(redcode_input.get("1.0", "end-1c").split("\n"), False)
        except:
            error_text = ""
            error_text += "The selected file could not be imported.\n"
            error_text += "It may contain compiler errors, be corrupt,\n"
            error_text += "or simply not contain a Redcode '94 load file."

            redcode_window.destroy()
            showinfo("Import Error", error_text)
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
        export_button.configure(state=ctk.DISABLED)
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
    export_button.configure(state=ctk.NORMAL)

    # The current_warrior variable is used in the below function
    current_warrior.id = len(o.warriors_temp) if current_edit_id is None else current_edit_id
    current_warrior.color = o.get_tile_color_from_id(current_warrior.id)
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
    edit_warrior_button.configure(state=ctk.NORMAL)
    remove_warrior_button.configure(state=ctk.NORMAL)
    redcode_window.destroy()

def save_warrior_as_load_file():
    # Writes the current warriors load file data to a .red file of user selection
    save_path = asksaveasfilename(title="Save Warrior", initialfile=f"{current_warrior.name if current_warrior.name != '' else 'Nameless'}.red", defaultextension="red", filetypes=[("Redcode '94 Load File", ".red"), ("All files", "*")], confirmoverwrite=True)

    try:
        with open(save_path, "w") as save_file:
            write_data = []
            # Save the warrior's code and other important data
            if current_warrior.name != '':
                write_data.append(f";name {current_warrior.name}")
            for line in current_warrior.load_file:
                write_data.append(o.parse_instruction_to_text(line))

            save_file.write("\n".join(write_data))

    except: return

def delete_warrior(id):
    o.warriors_temp.pop(id)
    display_warriors()
    if o.warriors_temp == []:
        edit_warrior_button.configure(state=ctk.DISABLED)
        remove_warrior_button.configure(state=ctk.DISABLED)

def open_state_window():
    global state_window, state_canvas, detail_button

    state_window_button.configure(state=ctk.DISABLED, text="Core Readout Active")

    state_window = ctk.CTkToplevel(o.root)
    state_window.resizable(False, False) # Consider making this resizable in the future; right now resizing it would break everything
    state_window.title("Core Readout")
    state_window.after(201, lambda: state_window.iconbitmap("assets/tailwind_icon.ico"))
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

    o.update_requested = True

def update_state_canvas():
    global state_window

    # Ignore if function is called when the window is not open
    if state_window is None or not state_window.winfo_exists(): return
    # Ignore if function is called while the render queue is empty
    if not o.update_requested: return
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

    o.update_requested = False
    
    # Copy updates to the previous state data
    o.prev_state_data = deepcopy(o.state_data)
        
def close_state_win():
    state_window_button.configure(state=ctk.NORMAL, text="View Core")
    state_window.destroy()

def open_detail_window():
    global detail_window, detail_target, search_value, info_labels, up_one_button, up_ten_button, down_one_button, down_ten_button

    detail_target = 0

    detail_button.configure(state=ctk.DISABLED, text="Detail Viewer Active")

    detail_window = ctk.CTkToplevel(o.root)
    detail_window.title("Core Details")
    detail_window.geometry("300x320" if o.deghost_button_enabled else "300x300")
    detail_window.resizable(False, False)
    detail_window.after(201, lambda: detail_window.iconbitmap("assets/tailwind_icon.ico"))
    detail_window.protocol("WM_DELETE_WINDOW", close_detail_win)

    search_value = ctk.StringVar()
    search_bar = ctk.CTkEntry(detail_window, textvariable=search_value, placeholder_text="Jump to Address...")
    search_value.trace_add("write", lambda _a, _b, _c: update_detail_window(search_value.get(), True))
    data_container = ctk.CTkFrame(detail_window, fg_color="black")
    options_container = ctk.CTkFrame(detail_window, width=30)

    info_labels = []
    for i in range(10):
        info_labels.append(ctk.CTkLabel(data_container))

    up_ten_button = ctk.CTkButton(options_container, text="-10", width=30, command=lambda: update_detail_window(detail_target - 10, False))
    up_one_button = ctk.CTkButton(options_container, text="↑", width=30, command=lambda: update_detail_window(detail_target - 1, False))
    down_one_button = ctk.CTkButton(options_container, text="↓", width=30, command=lambda: update_detail_window(detail_target + 1, False))
    down_ten_button = ctk.CTkButton(options_container, text="+10", width=30, command=lambda: update_detail_window(detail_target + 10, False))

    deghost_button = ctk.CTkButton(detail_window, text="Redraw Core", command=deghost)

    search_bar.grid(row=0, column=0, columnspan=2, sticky="nsew")
    data_container.grid(row=1, column=0, sticky="nsew")
    options_container.grid(row=1, column=1, sticky="ns")

    if o.deghost_button_enabled:
        deghost_button.grid(row=2, column=0, columnspan=2, sticky="nsew")

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
    options_container.grid_columnconfigure(0, weight=1)

    update_detail_window(detail_target, False)

def update_detail_window(target, from_search):
    global detail_target, info_labels, search_value

    if not from_search:
        search_value.set("")

    if type(target) != int:
        # Target value comes from search bar
        try: target = int(target)
        except: return

    if target < 0:
        update_detail_window(o.field_size + target, from_search)
        return
    if target > o.field_size:
        update_detail_window(target % o.field_size, from_search)
        return

    for i in range(len(o.state_data)):
        o.state_data[i].highlighted = False
    
    detail_target = target
    for i in range(len(info_labels)):
        target = (detail_target + i) % o.field_size
        info_labels[i].configure(text=f" #{str(target).zfill(4 if o.field_size < 10000 else 5)}: {o.parse_instruction_to_text(o.state_data[target].instruction)}")
        info_labels[i].configure(text_color=o.get_tile_hex_color(o.state_data[target].color) if o.state_data[target].color != "black" else "white")
        info_labels[i].configure(font=("Consolas", 15))
        o.state_data[target].highlighted = True

    # Buttons need to be locked to prevent the insane race condition that I cannot trace
    th.Thread(target=lock_detail_buttons).start()
    o.update_requested = True

def lock_detail_buttons():
    global up_one_button, up_ten_button, down_one_button, down_ten_button

    up_one_button.configure(state=ctk.DISABLED, width=35)
    up_ten_button.configure(state=ctk.DISABLED, width=35)
    down_one_button.configure(state=ctk.DISABLED, width=35)
    down_ten_button.configure(state=ctk.DISABLED, width=35)
    sleep(0.01)
    up_one_button.configure(state=ctk.NORMAL, width=30)
    up_ten_button.configure(state=ctk.NORMAL, width=30)
    down_one_button.configure(state=ctk.NORMAL, width=30)
    down_ten_button.configure(state=ctk.NORMAL, width=30)

def deghost():
    # Janky fix for ghost highlights problem on slower systems
    # This simply forces a core redraw from scratch
    for i in range(len(o.state_data)):
        o.state_data[i].highlighted = False
    o.prev_state_data = []
    o.update_requested = True
    update_detail_window(detail_target, False)

def close_detail_win():
    for i in range(len(o.state_data)):
        o.state_data[i].highlighted = False
    o.prev_state_data = []
    o.update_requested = True
    try: detail_button.configure(state=ctk.NORMAL, text="Open Detail Viewer")
    except: pass
    detail_window.destroy()

def update_core_label():
    # Create text to be displayed on the root core readout
    if core_label is None or o.state_data == []: return

    core_text = ""
    core_text += f"Cycle {o.cur_cycle:0{len(str(o.max_cycle_count))}}/{o.max_cycle_count}\n"
    if not o.sim_completed:
        core_text += f"Warriors Remaining: {len(o.warriors_temp)}"
    elif len(o.warriors_temp) == 1:
        core_text += f"Winner: {o.warriors_temp[0].name} ({o.warriors_temp[0].color})"
    else:
        core_text += "Draw"
    
    core_label.configure(text=core_text)

def open_options_menu():
    options_window = ctk.CTkToplevel(o.root)
    options_window.geometry("250x200")
    options_window.resizable(False, False)
    options_window.title("Program Options")
    options_window.after(201, lambda: options_window.iconbitmap("assets/tailwind_icon.ico"))
    options_window.grab_set()

    credits_text = ""
    credits_text += "Developed by Nils K (Quadratic) for Indirect UF\n"
    credits_text += "Inspired by pMARS, CoreWin and the defunct corewar.io\n"
    credits_text += "Libraries used: customtkinter, PIL, pyperclip & dependencies\n"
    credits_text += "Probably dedicated to someone, IDK"

    dark_mode_toggle = ctk.CTkCheckBox(options_window, command=o.toggle_dark_mode, text="Dark Mode")
    deghost_toggle = ctk.CTkCheckBox(options_window, command=o.toggle_deghost, text="Show 'redraw core' button\n(use in case of ghost highlights)")
    credits_button = ctk.CTkButton(options_window, command=lambda: showinfo(title="Tailwind Redcode Simulator: Credits", message=credits_text), text="Credits")

    dark_mode_toggle.grid(row=0, column=0, sticky="ew")
    deghost_toggle.grid(row=1, column=0, sticky="ew")
    credits_button.grid(row=3, column=0, sticky="ns")

    options_window.grid_rowconfigure(list(range(4)), weight=1)
    options_window.grid_columnconfigure(0, weight=1)

    # Set options as needed
    if ctk.get_appearance_mode() == "Dark": dark_mode_toggle.select()
    if o.deghost_button_enabled: deghost_toggle.select()

main()
o.root.mainloop()
