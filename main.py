# The main program file; acts primarily as UI manager
print("Log active, launching Tailwind v0.8...")

import customtkinter as ctk
from tkinter.messagebox import showinfo
from tkinter.filedialog import asksaveasfilename, askopenfilename
import math
import threading as th
import json
from PIL import ImageTk
from ctypes import windll
from random import randint
from time import sleep
from pyperclip import copy
from copy import deepcopy
from os import listdir
import graphics
import options as o
import compiler
import process

# Global variables are declared in options.py

o.root.geometry("450x200")
o.root.resizable(False, False)
o.root.title("Tailwind v0.8")
o.root.protocol("WM_DELETE_WINDOW", o.close_all_threads)

# Create the main UI class
class App():
    def __init__(self):
        # These need to be declared here as their existence is required by several functions
        self.state_window = None
        self.detail_window = None
        self.core_label = None

        self.sim_thread = None

        # These are only used by the Redcode editor, but must be global as they need to be tracked between functions
        self.current_warrior = None
        self.current_edit_id = None
        self.current_selection = ctk.IntVar(value=0)

        # Do initial setup based on user configuration
        self.load_user_config()

        # Start the background threads; graphics and simulation
        self.sim_thread = th.Thread(target=process.simulation_clock)
        self.sim_thread.start()
        self.render_state()

        # Create UI elements for the main window
        self.top_container = ctk.CTkFrame(o.root)
        self.state_window_button = ctk.CTkButton(self.top_container, text="View Core", command=self.open_state_window, state=ctk.DISABLED)
        self.setup_button = ctk.CTkButton(self.top_container, text="Setup", command=self.open_setup_menu)
        self.help_button = ctk.CTkButton(self.top_container, text="Help [WIP]", state=ctk.DISABLED)
        self.options_button = ctk.CTkButton(self.top_container, text="Options", command=self.open_options_menu)

        self.bottom_container = ctk.CTkFrame(o.root)
        self.speed_control = ctk.CTkSlider(self.bottom_container, from_=0, to=9, number_of_steps=9, orientation=ctk.HORIZONTAL, command=self.change_speed)
        self.speed_display = ctk.CTkLabel(self.bottom_container, text="1x", width=35)
        self.max_speed_button = ctk.CTkCheckBox(self.bottom_container, text="Max. Simulation Speed", command=lambda: self.change_speed("max"))
        self.pause_button = ctk.CTkButton(self.bottom_container, text="Start", command=self.toggle_pause, state=ctk.DISABLED)
        self.one_step_button = ctk.CTkButton(self.bottom_container, text="Advance One Cycle", command=lambda: process.simulation_clock(True), state=ctk.DISABLED)

        self.core_frame = ctk.CTkFrame(self.bottom_container, fg_color="black")
        self.core_label = ctk.CTkLabel(self.core_frame, text="No Core Loaded...", text_color="white", font=("Consolas", 12), anchor="w", justify="left")

        self.top_container.grid(row=0, column=0, sticky="nsew")
        self.bottom_container.grid(row=2, column=0, sticky="nsew")

        self.state_window_button.grid(row=0, column=0, rowspan=3, sticky="nsew")
        self.setup_button.grid(row=0, column=2, rowspan=3, sticky="nsew")
        self.help_button.grid(row=0, column=4, sticky="nsew")
        self.options_button.grid(row=2, column=4, sticky="nsew")

        self.pause_button.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.speed_control.grid(row=1, column=0, sticky="ew")
        self.speed_display.grid(row=1, column=1, sticky="nsew")
        self.max_speed_button.grid(row=2, column=0, sticky="nsew")
        self.one_step_button.grid(row=0, column=3, sticky="nsew")

        self.core_frame.grid(row=2, column=2, columnspan=2, sticky="nsew")
        self.core_label.grid(row=0, column=1, sticky="nsew")

        o.root.grid_rowconfigure([0, 2], weight=1)
        o.root.grid_rowconfigure(1, weight=3)
        o.root.grid_columnconfigure(0, weight=1)

        self.top_container.grid_rowconfigure(1, weight=1)
        self.top_container.grid_columnconfigure([1, 3], weight=1)

        self.bottom_container.grid_rowconfigure(2, weight=1)
        self.bottom_container.grid_columnconfigure(2, weight=1)

        self.core_frame.grid_rowconfigure(0, weight=1)
        self.core_frame.grid_columnconfigure(0, weight=1)
        self.core_frame.grid_columnconfigure(1, weight=10)

        self.speed_control.set(0)

    def render_state(self):
        # Runs five times per second; executes the render queue and checks for simulation completion
            self.update_core_label()
            if o.update_requested:
                self.update_state_canvas()
                
            if o.sim_completed:
                # End the simulation
                if not o.paused: self.toggle_pause()
                self.pause_button.configure(text="Simulation Complete", state=ctk.DISABLED)
                self.one_step_button.configure(state=ctk.DISABLED)
            
            o.root.after(20, self.render_state)

    def change_speed(self, new_speed):
        if new_speed == "max":
            # Max speed button is checked
            o.max_speed_enabled = not o.max_speed_enabled
            return

        o.play_speed = o.speed_levels[math.floor(new_speed)]
            
        self.speed_display.configure(text=f"{o.play_speed}x")

    def toggle_pause(self):
        if o.paused:
            self.pause_button.configure(text="Pause")
            self.one_step_button.configure(state=ctk.DISABLED)
            o.paused = False
        else:
            self.pause_button.configure(text="Unpause")
            self.one_step_button.configure(state=ctk.NORMAL)
            o.paused = True
            o.update_requested = True # Ensure rendering is caught up with state

    def open_setup_menu(self):
        if not o.paused: self.toggle_pause()

        self.setup_window = ctk.CTkToplevel(o.root)
        self.setup_window.title("Match Options")
        self.setup_window.geometry("500x275")
        self.setup_window.resizable(False, False)
        self.setup_window.after(201, lambda: self.setup_window.iconbitmap(f"assets/icons/icon_{o.user_config['selected_theme']}.ico")) # Workaround for a silly CTk behaviour which sets the icon only after 200ms
        self.setup_window.grab_set()

        o.warriors_temp = deepcopy(o.warriors) # Reset all unsaved warriors

        random_core = ctk.IntVar()

        self.warrior_container = ctk.CTkFrame(self.setup_window)
        self.warrior_label = ctk.CTkLabel(self.warrior_container, font=("TkDefaultFont", 14), text="Warriors")
        self.warrior_list_container = ctk.CTkScrollableFrame(self.warrior_container, width=150, height=200, bg_color="gray39")
        self.add_warrior_button = ctk.CTkButton(self.warrior_container, text="Create Warrior", command=lambda: self.open_redcode_window(None))
        self.import_warrior_button = ctk.CTkButton(self.warrior_container, text="Import Load File", command=self.import_load_file)
        self.edit_warrior_button = ctk.CTkButton(self.warrior_container, text="Edit Selected", command=lambda: self.open_redcode_window(o.warriors_temp[self.current_selection.get()]), state=ctk.DISABLED if o.warriors == [] else ctk.NORMAL)
        self.remove_warrior_button = ctk.CTkButton(self.warrior_container, text="Remove Selected", command=lambda: self.delete_warrior(self.current_selection.get()), state=ctk.DISABLED if o.warriors == [] else ctk.NORMAL)

        self.core_size_container = ctk.CTkFrame(self.setup_window)
        self.core_size_label = ctk.CTkLabel(self.core_size_container, font=("TkDefaultFont", 14), text="Core Size")
        self.core_size_input = ctk.CTkEntry(self.core_size_container, placeholder_text="Size...")
        self.random_button = ctk.CTkCheckBox(self.core_size_container, text="Random", command=lambda: self.core_size_input.configure(state=ctk.DISABLED if self.random_button.get() == 1 else ctk.NORMAL), variable=random_core)

        self.misc_container = ctk.CTkFrame(self.setup_window)
        self.misc_label = ctk.CTkLabel(self.misc_container, font=("TkDefaultFont", 14), text="Miscellaneous")
        self.max_cycle_label = ctk.CTkLabel(self.misc_container, text="Max. Cycles:")
        self.max_cycle_input = ctk.CTkEntry(self.misc_container, placeholder_text="Cycles...")
        self.max_length_label = ctk.CTkLabel(self.misc_container, text="Max. Program Length:")
        self.max_length_input = ctk.CTkEntry(self.misc_container, placeholder_text="Length...")

        self.error_label = ctk.CTkLabel(self.setup_window, text_color="red", text="")
        self.apply_button = ctk.CTkButton(self.setup_window, text="Apply", command=lambda: self.apply_setup(self.core_size_input.get(), self.max_cycle_input.get(), self.max_length_input.get(), random_core.get()))

        self.warrior_container.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.core_size_container.grid(row=0, column=2, sticky="new")
        self.misc_container.grid(row=1, column=2, sticky="sw")

        self.warrior_label.grid(row=1, column=1, columnspan=2, sticky="nsew")
        self.warrior_list_container.grid(row=2, column=1, rowspan=8, sticky="nsew")
        self.add_warrior_button.grid(row=2, column=2, sticky="nsew")
        self.import_warrior_button.grid(row=4, column=2, sticky="nsew")
        self.edit_warrior_button.grid(row=6, column=2, sticky="nsew")
        self.remove_warrior_button.grid(row=8, column=2, sticky="nsew")

        self.core_size_label.grid(row=0, column=0, sticky="nsew")
        self.core_size_input.grid(row=1, column=0, sticky="nsew")
        self.random_button.grid(row=2, column=0, sticky="nsew")

        self.misc_label.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.max_cycle_label.grid(row=1, column=0, sticky="nsew")
        self.max_cycle_input.grid(row=2, column=0, sticky="nsew")
        self.max_length_label.grid(row=4, column=0, sticky="nsew")
        self.max_length_input.grid(row=5, column=0, sticky="nsew")

        self.error_label.grid(row=2, column=0, columnspan=3, sticky="nsew")
        self.apply_button.grid(row=3, column=0, columnspan=3, sticky="sew")

        self.setup_window.grid_rowconfigure([0, 1, 2], weight=1)
        self.setup_window.grid_columnconfigure(1, weight=1)

        self.warrior_container.grid_rowconfigure(list(range(2, 9)), weight=1)

        self.misc_container.grid_rowconfigure([2, 3, 5], weight=1)

        self.core_size_input.insert(0, o.field_size)
        self.max_cycle_input.insert(0, o.max_cycle_count)
        self.max_length_input.insert(0, o.max_program_length)

        self.display_warriors()

    def display_warriors(self):
        for child in self.warrior_list_container.winfo_children():
            child.destroy()

        i = 0
        for warrior in o.warriors_temp:
            display_color = o.get_tile_hex_color(warrior.color)
            if len(warrior.name) > 13:
                display_name = warrior.name[0:13] + "..."
            else:
                display_name = warrior.name
            new_warrior = ctk.CTkRadioButton(self.warrior_list_container, width=140, height=30, fg_color=display_color, hover_color=display_color, font=("Consolas", 13), text=display_name, variable=self.current_selection, value=i)
            new_warrior.grid(row=i, column=0, sticky="nsew")
            i += 1

    def apply_setup(self, core_size, max_cycles, max_length, random_core):
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
            self.error_label.configure(text="One or more parameters has an invalid value")
            return

        if o.warriors_temp == []:
            self.error_label.configure(text="Cannot begin a match with no warriors in core")
            return
        
        if core_size < max_length * len(o.warriors_temp):
            self.error_label.configure(text="Core size cannot be smaller than max. warrior length * warrior count")
            return
        
        # Save/reset data in preparation for match
        o.sim_completed = False
        o.cur_cycle = 0

        o.field_size = core_size
        o.max_cycle_count = max_cycles
        o.max_program_length = max_length

        o.warriors = deepcopy(o.warriors_temp)
        o.initialize_core()

        if self.detail_window is not None:
            self.close_detail_win()
        if self.state_window is not None:
            self.close_state_win()
        else:
            self.state_window_button.configure(text="View Core", state=ctk.NORMAL)

        self.pause_button.configure(text="Start", state=ctk.NORMAL)
        self.one_step_button.configure(state=ctk.NORMAL)
        self.setup_window.destroy()

    def import_load_file(self):
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
        
        self.open_redcode_window(o.Warrior(None, None, None, load_data, None))

    def open_redcode_window(self, warrior):
        self.redcode_window = ctk.CTkToplevel(o.root)
        self.redcode_window.geometry("800x600")
        self.redcode_window.resizable(False, False)
        self.redcode_window.title("Tailwind Redcode Editor")
        self.redcode_window.after(201, lambda: self.redcode_window.iconbitmap(f"assets/icons/icon_{o.user_config['selected_theme']}.ico"))
        self.redcode_window.grab_set()

        self.redcode_input = ctk.CTkTextbox(self.redcode_window, font=("Consolas", 12), height=580, wrap=ctk.NONE)

        self.compiled_container = ctk.CTkScrollableFrame(self.redcode_window)
        self.compiled_header = ctk.CTkLabel(self.compiled_container, anchor="w", text="Parsed Redcode:")
        self.compiled_display = ctk.CTkLabel(self.compiled_container, font=("Consolas", 14), anchor="w", justify="left", text="No current output")

        self.button_container = ctk.CTkFrame(self.redcode_window)
        self.debug_button = ctk.CTkCheckBox(self.button_container, text="Enable debug output (slow)")
        self.compile_button = ctk.CTkButton(self.button_container, command=lambda: self.compile_warrior(self.redcode_input.get("1.0", "end-1c").split("\n"), bool(self.debug_button.get())), text="Compile")
        self.save_button = ctk.CTkButton(self.button_container, text="Add to Core", state=ctk.DISABLED, command=self.add_current_warrior_to_list)
        self.export_button = ctk.CTkButton(self.button_container, text="Save as File", command=self.save_warrior_as_load_file, state=ctk.DISABLED)
        self.clip_button = ctk.CTkButton(self.button_container, text="Copy to Clipboard", command=lambda: copy(self.compiled_display.cget("text")), state=ctk.DISABLED)

        self.redcode_input.grid(row=0, column=0, rowspan=3, sticky="nsew")

        self.compiled_container.grid(row=0, column=1, sticky="nsew")
        self.compiled_header.grid(row=0, column=0, sticky="ew")
        self.compiled_display.grid(row=1, column=0, sticky="nsew")

        self.button_container.grid(row=2, column=1, sticky="nsew")
        self.debug_button.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.compile_button.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.save_button.grid(row=2, column=0, rowspan=2, sticky="nsew")
        self.export_button.grid(row=2, column=1, sticky="nsew")
        self.clip_button.grid(row=3, column=1, sticky="nsew")

        self.redcode_window.grid_columnconfigure(0, weight=2)
        self.redcode_window.grid_columnconfigure(1, weight=1)
        self.redcode_window.grid_rowconfigure(0, weight=10)
        self.redcode_window.grid_rowconfigure([1, 2], weight=1)

        self.compiled_container.grid_rowconfigure(0, weight=1)
        self.compiled_container.grid_rowconfigure(1, weight=10)
        self.compiled_container.grid_columnconfigure(0, weight=1)

        self.button_container.grid_rowconfigure([1, 2, 3], weight=1)
        self.button_container.grid_columnconfigure([0, 1], weight=1)

        if warrior is not None:
            try:
                # Editing an extant warrior; needs to insert its data
                self.current_warrior = warrior
                self.current_edit_id = warrior.id
                self.redcode_input.insert("1.0", "\n".join(warrior.raw_data))

                # Precompile the aforementioned warrior
                self.compile_warrior(self.redcode_input.get("1.0", "end-1c").split("\n"), False)
            except:
                error_text = ""
                error_text += "The selected file could not be imported.\n"
                error_text += "It may contain compiler errors, be corrupt,\n"
                error_text += "or simply not contain a Redcode '94 load file."

                self.redcode_window.destroy()
                showinfo("Import Error", error_text)
        else:
            self.current_warrior = None
            self.current_edit_id = None

    # Creates a warrior from text data entered by user
    def compile_warrior(self, data, debug):
        self.current_warrior, error_list = compiler.compile_load_file(data, debug)
        if error_list != []:
            # Errors are present
            self.compiled_display.configure(text_color="red", font=("Consolas", 12), text=f"({len(error_list)} errors)\n{'\n'.join(error_list)}")

            self.save_button.configure(state=ctk.DISABLED)
            self.clip_button.configure(state=ctk.DISABLED)
            self.export_button.configure(state=ctk.DISABLED)
            return

        load_text = []
        for line in self.current_warrior.load_file:
            load_text.append(o.parse_instruction_to_text(line))

        if load_text == []:
            self.compiled_display.configure(text_color=("black", "white"), text="No readable lines")
            return

        self.compiled_display.configure(text_color=("black", "white"), font=("Consolas", 14), text="\n".join(load_text))

        self.save_button.configure(state=ctk.NORMAL)
        self.clip_button.configure(state=ctk.NORMAL)
        self.export_button.configure(state=ctk.NORMAL)

        # The current_warrior variable is used in the below function
        self.current_warrior.id = len(o.warriors_temp) if self.current_edit_id is None else self.current_edit_id
        self.current_warrior.color = o.get_tile_color_from_id(self.current_warrior.id)
        self.current_warrior.raw_data = data

    def add_current_warrior_to_list(self):
        # This function uses global parameters set at compile-time
        if self.current_edit_id is None:
            o.warriors_temp.append(self.current_warrior)
        else:
            # If current_edit_id is set, overwrite the warrior of that id
            for i in range(len(o.warriors_temp)):
                if o.warriors_temp[i].id == self.current_edit_id:
                    o.warriors_temp[i] = self.current_warrior

        self.display_warriors()
        self.edit_warrior_button.configure(state=ctk.NORMAL)
        self.remove_warrior_button.configure(state=ctk.NORMAL)
        self.redcode_window.destroy()

    def save_warrior_as_load_file(self):
        # Writes the current warriors load file data to a .red file of user selection
        save_path = asksaveasfilename(title="Save Warrior", initialfile=f"{self.current_warrior.name if self.current_warrior.name != '' else 'Nameless'}.red", defaultextension="red", filetypes=[("Redcode '94 Load File", ".red"), ("All files", "*")], confirmoverwrite=True)

        try:
            with open(save_path, "w") as save_file:
                write_data = []
                # Save the warrior's code and other important data
                if self.current_warrior.name != '':
                    write_data.append(f";name {self.current_warrior.name}")
                for line in self.current_warrior.load_file:
                    write_data.append(o.parse_instruction_to_text(line))

                save_file.write("\n".join(write_data))

        except:
            showinfo("Export Error", "The warrior could not be exported.\nIf the issue persists, please report this issue via Indirect UF contact channels.")
            return

    def delete_warrior(self, id):
        o.warriors_temp.pop(id)
        self.display_warriors()
        if o.warriors_temp == []:
            self.edit_warrior_button.configure(state=ctk.DISABLED)
            self.remove_warrior_button.configure(state=ctk.DISABLED)

    def open_state_window(self):
        self.state_window_button.configure(state=ctk.DISABLED, text="Core Readout Active")

        self.state_window = ctk.CTkToplevel(o.root)
        self.state_window.resizable(False, False) # Consider making this resizable in the future; right now resizing it would break everything
        self.state_window.title("Core Readout")
        self.state_window.after(201, lambda: self.state_window.iconbitmap(f"assets/icons/icon_{o.user_config['selected_theme']}.ico"))
        self.state_window.protocol("WM_DELETE_WINDOW", self.close_state_win)

        self.state_canvas = ctk.CTkCanvas(self.state_window, bg="black")
        
        self.bottom_bar_container = ctk.CTkFrame(self.state_window, width=0, height=0)
        self.pspace_button = ctk.CTkButton(self.bottom_bar_container, text="View P-Space [WIP]", state=ctk.DISABLED)
        self.detail_button = ctk.CTkButton(self.bottom_bar_container, command=self.open_detail_window, text="Open Detail Viewer")

        self.state_canvas.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.bottom_bar_container.grid(row=1, column=0, sticky="nsew")
        self.pspace_button.grid(row=0, column=5, sticky="nsew")
        self.detail_button.grid(row=0, column=6, sticky="nsew")

        self.state_window.grid_rowconfigure(0, weight=1)
        self.state_window.grid_rowconfigure(1, weight=0) # All widgets on this row are forced to their minimum size
        self.state_window.grid_columnconfigure(0, weight=1)

        self.bottom_bar_container.grid_rowconfigure([0, 1], weight=1)
        self.bottom_bar_container.grid_columnconfigure([0, 2, 6], weight=10)
        self.bottom_bar_container.grid_columnconfigure([1, 3], weight=1)
        self.bottom_bar_container.grid_columnconfigure(4, weight=20)

        o.update_requested = True

    def update_state_canvas(self):
        # Ignore if function is called when the window is not open
        if self.state_window is None or not self.state_window.winfo_exists(): return
        # Ignore if function is called while the render queue is empty
        if not o.update_requested: return
        # If core is unloaded while window is open, close it
        if o.state_data == []: self.state_window.destroy()

        o.state_image = graphics.create_image_from_state_data(o.state_data, o.prev_state_data, o.field_size, o.state_image)
        o.resized_state_image = o.state_image.resize((800, round(o.state_image.height * (800 / o.state_image.width))))
        o.root.display_image = display_image = ImageTk.PhotoImage(o.resized_state_image)
        self.state_canvas.create_image((405, o.resized_state_image.height // 2 + 5), image=display_image)

        # The next step breaks if the Windows scaling setting is above 100%, hence that needs to be checked for
        scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100

        # Recalculate window size based on the size of the image; 40px margin for the border and bottom bar
        self.state_window.geometry(f"{round(810 / scale_factor)}x{round(o.resized_state_image.height / scale_factor) + 40}")

        o.update_requested = False
        
        # Copy updates to the previous state data
        o.prev_state_data = deepcopy(o.state_data)
        
    def close_state_win(self):
        self.state_window_button.configure(state=ctk.NORMAL, text="View Core")
        self.state_window.destroy()

    def open_detail_window(self):
        self.detail_target = 0

        self.detail_button.configure(state=ctk.DISABLED, text="Detail Viewer Active")

        self.detail_window = ctk.CTkToplevel(o.root)
        self.detail_window.title("Core Details")
        self.detail_window.geometry("300x320")
        self.detail_window.resizable(False, False)
        self.detail_window.after(201, lambda: self.detail_window.iconbitmap(f"assets/icons/icon_{o.user_config['selected_theme']}.ico"))
        self.detail_window.protocol("WM_DELETE_WINDOW", self.close_detail_win)

        self.search_value = ctk.StringVar()
        self.search_bar = ctk.CTkEntry(self.detail_window, textvariable=self.search_value, placeholder_text="Jump to Address...")
        self.search_value.trace_add("write", lambda _a, _b, _c: self.update_detail_window(self.search_value.get(), True))
        self.data_container = ctk.CTkFrame(self.detail_window, fg_color="black")
        self.options_container = ctk.CTkFrame(self.detail_window, width=30)
        self.bottom_container = ctk.CTkFrame(self.detail_window)

        self.info_labels = []
        for i in range(10):
            self.info_labels.append(ctk.CTkLabel(self.data_container))

        self.up_ten_button = ctk.CTkButton(self.options_container, text="-10", width=30, command=lambda: self.update_detail_window(self.detail_target - 10, False))
        self.up_one_button = ctk.CTkButton(self.options_container, text="↑", width=30, command=lambda: self.update_detail_window(self.detail_target - 1, False))
        self.down_one_button = ctk.CTkButton(self.options_container, text="↓", width=30, command=lambda: self.update_detail_window(self.detail_target + 1, False))
        self.down_ten_button = ctk.CTkButton(self.options_container, text="+10", width=30, command=lambda: self.update_detail_window(self.detail_target + 10, False))

        self.refresh_button = ctk.CTkButton(self.bottom_container, text="Refresh", command=lambda: self.update_detail_window(self.detail_target, False))
        self.deghost_button = ctk.CTkButton(self.bottom_container, text="Redraw Core", command=self.deghost)

        self.search_bar.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.data_container.grid(row=1, column=0, sticky="nsew")
        self.options_container.grid(row=1, column=1, sticky="ns")

        self.bottom_container.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.refresh_button.grid(row=0, column=0, columnspan=2 if not o.deghost_button_enabled else 1, sticky="nsew")
        if o.deghost_button_enabled:
            self.deghost_button.grid(row=0, column=1, sticky="nsew")

        for i in range(len(self.info_labels)):
            self.info_labels[i].grid(row=i, column=0, sticky="nsew")

        self.up_ten_button.grid(row=0, column=0, sticky="nsew")
        self.up_one_button.grid(row=1, column=0, sticky="nsew")
        self.down_one_button.grid(row=2, column=0, sticky="nsew")
        self.down_ten_button.grid(row=3, column=0, sticky="nsew")

        self.detail_window.grid_rowconfigure(1, weight=1)
        self.detail_window.grid_columnconfigure(0, weight=1)

        self.data_container.grid_rowconfigure(list(range(len(self.info_labels) + 1)), weight=1)

        self.options_container.grid_rowconfigure([0, 1, 2, 3], weight=1)
        self.options_container.grid_columnconfigure(0, weight=1)

        self.bottom_container.grid_rowconfigure(0, weight=1)
        self.bottom_container.grid_columnconfigure([0, 1], weight=1)

        self.update_detail_window(self.detail_target, False)

    def update_detail_window(self, target, from_search):
        if not from_search:
            self.search_value.set("")

        if type(target) != int:
            # Target value comes from search bar
            try: target = int(target)
            except: return

        if target < 0:
            self.update_detail_window(o.field_size + target, from_search)
            return
        if target > o.field_size:
            self.update_detail_window(target % o.field_size, from_search)
            return

        for i in range(len(o.state_data)):
            o.state_data[i].highlighted = False
        
        self.detail_target = target
        for i in range(len(self.info_labels)):
            target = (self.detail_target + i) % o.field_size
            self.info_labels[i].configure(text=f" #{str(target).zfill(4 if o.field_size < 10000 else 5)}: {o.parse_instruction_to_text(o.state_data[target].instruction)}")
            self.info_labels[i].configure(text_color=o.get_tile_hex_color(o.state_data[target].color) if o.state_data[target].color != "black" else "white")
            self.info_labels[i].configure(font=("Consolas", 15))
            o.state_data[target].highlighted = True

        # Buttons need to be locked to prevent the insane race condition that I cannot trace
        th.Thread(target=self.lock_detail_buttons).start()
        o.update_requested = True

    def lock_detail_buttons(self):
        self.up_one_button.configure(state=ctk.DISABLED, width=35)
        self.up_ten_button.configure(state=ctk.DISABLED, width=35)
        self.down_one_button.configure(state=ctk.DISABLED, width=35)
        self.down_ten_button.configure(state=ctk.DISABLED, width=35)
        self.refresh_button.configure(state=ctk.DISABLED)
        sleep(0.01)
        self.up_one_button.configure(state=ctk.NORMAL, width=30)
        self.up_ten_button.configure(state=ctk.NORMAL, width=30)
        self.down_one_button.configure(state=ctk.NORMAL, width=30)
        self.down_ten_button.configure(state=ctk.NORMAL, width=30)
        self.refresh_button.configure(state=ctk.NORMAL)

    def deghost(self):
        # Janky fix for ghost highlights problem on slower systems
        # This simply forces a core redraw from scratch
        for i in range(len(o.state_data)):
            o.state_data[i].highlighted = False
        o.prev_state_data = []
        o.update_requested = True
        self.update_detail_window(self.detail_target, False)

    def close_detail_win(self):
        for i in range(len(o.state_data)):
            o.state_data[i].highlighted = False
        o.prev_state_data = []
        o.update_requested = True
        try: self.detail_button.configure(state=ctk.NORMAL, text="Open Detail Viewer")
        except: pass
        self.detail_window.destroy()

    def update_core_label(self):
        # Create text to be displayed on the root core readout
        if self.core_label is None or o.state_data == []: return

        core_text = ""
        core_text += f"Cycle {o.cur_cycle:0{len(str(o.max_cycle_count))}}/{o.max_cycle_count}\n"
        if not o.sim_completed:
            core_text += f"Warriors Remaining: {len(o.warriors_temp)}"
        elif len(o.warriors_temp) == 1:
            core_text += f"Winner: {o.warriors_temp[0].name} ({o.warriors_temp[0].color})"
        else:
            core_text += "Draw"
        
        self.core_label.configure(text=core_text)

    def open_options_menu(self):
        self.options_window = ctk.CTkToplevel(o.root)
        self.options_window.geometry("250x200")
        self.options_window.resizable(False, False)
        self.options_window.title("Options")
        self.options_window.after(201, lambda: self.options_window.iconbitmap(f"assets/icons/icon_{o.user_config['selected_theme']}.ico"))
        self.options_window.grab_set()
        self.options_window.protocol("WM_DELETE_WINDOW", self.close_options_win)

        credits_text = ""
        credits_text += "Developed by Nils K (Quadratic) for Indirect UF\n"
        credits_text += "Inspired by pMARS, CoreWin and the defunct corewar.io\n"
        credits_text += "Libraries used: customtkinter, PIL, pyperclip & dependencies\n"
        credits_text += "Probably dedicated to someone, IDK"

        self.deghost_toggle = ctk.CTkCheckBox(self.options_window, command=o.toggle_deghost, text="Show 'redraw core' button\n(use in case of ghost highlights)")
        self.theme_settings_container = ctk.CTkFrame(self.options_window)
        self.credits_button = ctk.CTkButton(self.options_window, command=lambda: showinfo(title="Tailwind Redcode Simulator: Credits", message=credits_text), text="Credits")

        self.theme_label = ctk.CTkLabel(self.theme_settings_container, text="Theme\n(changes require restart)")
        self.theme_selector = ctk.CTkOptionMenu(self.theme_settings_container, command=o.set_theme)
        self.dark_mode_toggle = ctk.CTkCheckBox(self.theme_settings_container, command=o.toggle_dark_mode, text="Dark Mode")

        self.deghost_toggle.grid(row=0, column=0, sticky="ew")
        self.theme_settings_container.grid(row=1, column=0, sticky="nsew")
        self.credits_button.grid(row=3, column=0, sticky="ns")

        self.theme_label.grid(row=0, column=0, sticky="ew")
        self.theme_selector.grid(row=1, column=0, sticky="nsew")
        self.dark_mode_toggle.grid(row=2, column=0, sticky="ew")

        self.options_window.grid_rowconfigure(list(range(4)), weight=1)
        self.options_window.grid_columnconfigure(0, weight=1)

        self.theme_settings_container.grid_rowconfigure(list(range(3)), weight=1)
        self.theme_settings_container.grid_columnconfigure(0, weight=1)

        # Set options as needed
        if ctk.get_appearance_mode() == "Dark": self.dark_mode_toggle.select()
        if o.deghost_button_enabled: self.deghost_toggle.select()

        # Configure the theme selector
        # Get all themes in assets/themes excluding the hardcoded default and the template
        themes = []
        for theme in listdir("assets/themes"):
            if theme == "template.json" or theme == "tailwind_blue.json": continue
            themes.append(theme.removesuffix(".json"))

        # The default theme should always be first in the list
        themes.insert(0, "tailwind_blue")

        self.theme_selector.configure(values=themes)
        try: self.theme_selector.set(o.user_config["selected_theme"])
        except: self.theme_selector.set("assets/themes/tailwind_blue.json")

    def close_options_win(self):
        self.save_user_config()
        self.options_window.destroy()

    def save_user_config(self):
        with open("tailwind.config", "w") as config_file:
            config_file.write(json.dumps(o.user_config))

    def load_user_config(self):
        try:
            with open("tailwind.config", "r") as config_file:
                # Set all options as required by the config file
                o.user_config = json.loads(config_file.read())
                if o.user_config["dark_mode_enabled"]:
                    ctk.set_appearance_mode("dark")
                else:
                    ctk.set_appearance_mode("light")
                o.deghost_button_enabled = o.user_config["deghost_button_enabled"]
                ctk.set_default_color_theme(f"assets/themes/{o.user_config['selected_theme']}.json")

        except FileNotFoundError:
            # Create a config file with default settings
            ctk.set_appearance_mode("system")
            ctk.set_default_color_theme("assets/themes/tailwind_blue.json")
            o.user_config["dark_mode_enabled"] = ctk.get_appearance_mode() == "Dark"
            o.user_config["deghost_button_enabled"] = False
            o.user_config["selected_theme"] = "tailwind_blue"
            self.save_user_config()
        
        # Set the root window's icon to the loaded theme
        o.root.iconbitmap(f"assets/icons/icon_{o.user_config['selected_theme']}.ico")

main = App()
print("Tailwind loaded successfully.")
o.root.mainloop()
