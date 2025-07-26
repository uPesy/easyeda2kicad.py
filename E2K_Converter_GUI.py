#!/usr/bin/env python3
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import re

class EasyEda2KiCadGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EasyEDA to KiCad Converter GUI")
        self.root.geometry("800x650")
        self.root.resizable(True, True)
        
        # Default output folder
        self.default_output = r"/home/usr/Documents/Kicad/easyeda2kicad"
        
        # Colours for variable texts
        self.ht_red = "#CF033D"     # RGB: 153, 0, 61
        self.ht_orange = "#FF9900"  # RGB: 0, 153, 61
        self.ht_yellow = "#FFCD00"  # RGB: 61, 0, 153
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create widgets
        self.create_widgets()
        
        # Initialize history data
        self.history = []
        
        # Try to load history or add a sample entry
        try:
            self.load_history()
        except Exception as e:
            print(f"Error loading history: {e}")
            # Add a sample entry
            self.history.append({
                'lcsc_id': 'C44471',
                'symbol': 'ACS712ELCTR-05B-T',
                'footprint': 'SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL',
                'model3d': 'SOIC-8_L4.9-W3.9-H1.7-LS6.0-P1.27'
            })
            self.update_history_display()
        
        # Check if easyeda2kicad is installed
        self.check_easyeda2kicad()
        
        # Bind Enter key to convert function
        self.root.bind('<Return>', lambda event: self.convert())

    def check_easyeda2kicad(self):
        try:
            subprocess.run(["easyeda2kicad", "--version"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=False)
        except FileNotFoundError:
            messagebox.showerror(
                "Error", 
                "easyeda2kicad not found! Please install it using:\n\npip install easyeda2kicad\n\nOr ensure it's in your PATH."
            )
    
    def create_widgets(self):
        # Header
        header = ttk.Label(self.main_frame, text="EasyEDA to KiCad Component Converter", 
                          font=('Arial', 12, 'bold'))
        header.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky="w")
        
        # LCSC ID entry
        ttk.Label(self.main_frame, text="LCSC ID:").grid(row=1, column=0, sticky="w", pady=5)
        
        self.lcsc_id_var = tk.StringVar()
        self.lcsc_id_entry = ttk.Entry(self.main_frame, textvariable=self.lcsc_id_var, width=40)
        self.lcsc_id_entry.grid(row=1, column=1, sticky="ew", pady=5)
        self.lcsc_id_entry.focus()
        
        ttk.Label(self.main_frame, text="(e.g., C2167080 or just 2167080)").grid(row=1, column=2, sticky="w", padx=5)
        
        # Output folder
        ttk.Label(self.main_frame, text="Output Folder:").grid(row=2, column=0, sticky="w", pady=5)
        
        self.output_folder_var = tk.StringVar(value=self.default_output)
        self.output_folder_entry = ttk.Entry(self.main_frame, textvariable=self.output_folder_var, width=40)
        self.output_folder_entry.grid(row=2, column=1, sticky="ew", pady=5)
        
        self.browse_button = ttk.Button(self.main_frame, text="Browse...", command=self.browse_output)
        self.browse_button.grid(row=2, column=2, sticky="w", padx=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(self.main_frame, text="Options")
        options_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)
        
        # Conversion Type Options
        conversion_frame = ttk.LabelFrame(options_frame, text="Conversion Type")
        conversion_frame.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        
        self.full_option = tk.BooleanVar(value=True)
        ttk.Checkbutton(conversion_frame, text="Full Package (--full)", 
                        variable=self.full_option, 
                        command=self.toggle_full_option).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        # Individual component options
        self.symbol_option = tk.BooleanVar(value=False)
        self.symbol_checkbox = ttk.Checkbutton(conversion_frame, text="Symbol (--symbol)", 
                                variable=self.symbol_option)
        self.symbol_checkbox.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        self.footprint_option = tk.BooleanVar(value=False)
        self.footprint_checkbox = ttk.Checkbutton(conversion_frame, text="Footprint (--footprint)", 
                                    variable=self.footprint_option)
        self.footprint_checkbox.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        
        self.model3d_option = tk.BooleanVar(value=False)
        self.model3d_checkbox = ttk.Checkbutton(conversion_frame, text="3D Model (--3d)", 
                                  variable=self.model3d_option)
        self.model3d_checkbox.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        
        # Additional Options
        additional_frame = ttk.LabelFrame(options_frame, text="Additional Options")
        additional_frame.grid(row=0, column=1, sticky="nw", padx=5, pady=5)
        
        self.v5_option = tk.BooleanVar(value=False)
        v5_checkbox = ttk.Checkbutton(additional_frame, text="KiCad v5.x Format (--v5)", 
                        variable=self.v5_option, command=self.toggle_v5_option)
        v5_checkbox.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        self.overwrite_option = tk.BooleanVar(value=False)
        ttk.Checkbutton(additional_frame, text="Overwrite Existing Files (--overwrite)", 
                        variable=self.overwrite_option).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # Initialize checkboxes state based on full_option
        self.toggle_full_option()
        
        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.convert_button = ttk.Button(button_frame, text="Convert", command=self.convert)
        self.convert_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_fields)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=5, column=0, columnspan=3, sticky="ew")
        
        # Console output
        ttk.Label(self.main_frame, text="Console Output:").grid(row=6, column=0, sticky="w", pady=(10, 0))
        
        self.console_frame = ttk.Frame(self.main_frame)
        self.console_frame.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=5)
        
        # Console text widget
        self.console = tk.Text(self.console_frame, height=15, width=70, wrap=tk.WORD)
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure text tags for colored output
        self.console.tag_configure("red_text", foreground=self.ht_red)
        self.console.tag_configure("orange_text", foreground=self.ht_orange)
        self.console.tag_configure("yellow_text", foreground=self.ht_yellow)
        
        scrollbar = ttk.Scrollbar(self.console_frame, orient="vertical", command=self.console.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=scrollbar.set)
        
        # History section
        ttk.Label(self.main_frame, text="Recent Conversions:").grid(row=8, column=0, sticky="w", pady=(10, 0))
        
        # Create a frame to hold the history treeview
        self.history_frame = ttk.Frame(self.main_frame)
        self.history_frame.grid(row=9, column=0, columnspan=3, sticky="nsew", pady=5)
        
        # Create the treeview columns
        columns = ("lcsc_id", "symbol", "footprint", "model3d")
        self.history_tree = ttk.Treeview(self.history_frame, columns=columns, show="headings", height=10)
        
        # Configure column headings
        self.history_tree.heading("lcsc_id", text="LCSC ID")
        self.history_tree.heading("symbol", text="Symbol")
        self.history_tree.heading("footprint", text="Footprint")
        self.history_tree.heading("model3d", text="3D Model")
        
        # Configure column widths
        self.history_tree.column("lcsc_id", width=80, anchor="w")
        self.history_tree.column("symbol", width=200, anchor="w")
        self.history_tree.column("footprint", width=200, anchor="w")
        self.history_tree.column("model3d", width=200, anchor="w")
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(self.history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar_frame = ttk.Frame(self.main_frame)
        h_scrollbar_frame.grid(row=10, column=0, columnspan=3, sticky="ew")
        h_scrollbar = ttk.Scrollbar(h_scrollbar_frame, orient="horizontal", command=self.history_tree.xview)
        h_scrollbar.pack(fill=tk.X)
        self.history_tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create colored labels frame that overlays the treeview
        self.overlay_frame = tk.Frame(self.history_frame)
        self.overlay_frame.place(in_=self.history_tree, x=0, y=0, relwidth=1, relheight=1)
        self.overlay_frame.lower(self.history_tree)  # Place behind treeview
        
        # Bind treeview events
        self.history_tree.bind("<ButtonRelease-1>", self.on_treeview_click)
        self.history_tree.bind("<Motion>", self.on_treeview_motion)
        
        # Configure grid weights
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(7, weight=1)
        self.main_frame.rowconfigure(9, weight=1)
        
        # Store colored labels
        self.colored_labels = {}
    
    def toggle_full_option(self):
        # If Full is selected, disable individual component options
        if self.full_option.get():
            self.symbol_checkbox.config(state=tk.DISABLED)
            self.footprint_checkbox.config(state=tk.DISABLED)
            self.model3d_checkbox.config(state=tk.DISABLED)
            
            # Reset individual options
            self.symbol_option.set(False)
            self.footprint_option.set(False)
            self.model3d_option.set(False)
        else:
            # Enable individual component options
            self.symbol_checkbox.config(state=tk.NORMAL)
            self.footprint_checkbox.config(state=tk.NORMAL)
            self.model3d_checkbox.config(state=tk.NORMAL)

    def toggle_v5_option(self):
        # If the user is turning ON the v5 option, show a warning
        if self.v5_option.get():
            proceed = messagebox.askquestion(
                "Warning - KiCad v5.x Format", 
                "KiCad v5.x format is legacy and not recommended for new projects.\n\n"
                "Are you sure you want to use the old format?\n\n"
                "Most modern KiCad projects use v6+ format.",
                icon='warning'
            )
            
            # If they choose not to proceed, uncheck the box
            if proceed != 'yes':
                self.v5_option.set(False)

    def browse_output(self):
        # Show warning before allowing folder selection
        proceed = messagebox.askquestion(
            "Warning", 
            "The default output folder is already configured for your workflow.\n\n"
            "Are you sure you want to change it?\n\n"
            "Changing it might require manual adjustment later.",
            icon='warning'
        )
        
        if proceed == 'yes':
            folder = filedialog.askdirectory()
            if folder:
                self.output_folder_var.set(folder)
    
    def clear_fields(self):
        self.lcsc_id_var.set("")
        self.console.delete(1.0, tk.END)
        self.lcsc_id_entry.focus()

    def normalize_lcsc_id(self, lcsc_id):
        # Remove any spaces
        lcsc_id = lcsc_id.strip()
        
        # If input is only digits, add 'C' prefix
        if lcsc_id.isdigit():
            return "C" + lcsc_id
        
        # If LCSC ID already starts with 'C', return as is
        if lcsc_id.upper().startswith('C') and lcsc_id[1:].isdigit():
            return lcsc_id.upper()
        
        # If input is invalid, return None
        return None
    
    def convert(self):
        # Check if convert button is disabled (already running a conversion)
        if str(self.convert_button['state']) == 'disabled':
            return
            
        lcsc_id = self.lcsc_id_var.get().strip()
        
        # Validate LCSC ID
        normalized_id = self.normalize_lcsc_id(lcsc_id)
        if not normalized_id:
            messagebox.showerror("Error", "Invalid LCSC ID. Please enter a valid LCSC ID (e.g., C2167080 or 2167080)")
            return
        
        # Update the entry with normalized ID
        self.lcsc_id_var.set(normalized_id)
        
        # Prepare output folder
        output_folder = self.output_folder_var.get().strip()
        if not output_folder:
            messagebox.showerror("Error", "Please specify an output folder")
            return
        
        # Check if no conversion option is selected
        if not self.full_option.get() and not any([
            self.symbol_option.get(),
            self.footprint_option.get(),
            self.model3d_option.get()
        ]):
            messagebox.showerror("Error", "Please select at least one conversion option (Full, Symbol, Footprint, or 3D Model)")
            return
        
        # Build command
        cmd = ["easyeda2kicad", "--lcsc_id=" + normalized_id]
        
        # Add conversion options
        if self.full_option.get():
            cmd.append("--full")
        else:
            if self.symbol_option.get():
                cmd.append("--symbol")
            if self.footprint_option.get():
                cmd.append("--footprint")
            if self.model3d_option.get():
                cmd.append("--3d")
        
        # Add additional options
        if self.v5_option.get():
            cmd.append("--v5")
        if self.overwrite_option.get():
            cmd.append("--overwrite")
        
        cmd.append("--output")
        cmd.append(output_folder)
        
        # Update status
        self.status_var.set(f"Converting {normalized_id}...")
        
        # Clear console
        self.console.delete(1.0, tk.END)
        
        # Disable convert button
        self.convert_button.config(state=tk.DISABLED)
        
        # Log command
        self.console.insert(tk.END, "Running command: " + " ".join(cmd) + "\n\n")
        
        # Run conversion in a separate thread
        threading.Thread(target=self.run_conversion, args=(cmd,)).start()
    
    def run_conversion(self, cmd):
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Variables to store component information
            symbol_name = None
            footprint_name = None
            model3d_name = None
            lcsc_id = self.lcsc_id_var.get()
            
            for line in process.stdout:
                # Extract component information from output
                if "Symbol name :" in line:
                    parts = line.split("Symbol name : ")
                    if len(parts) > 1:
                        symbol_name = parts[1].strip()
                        
                    # Mark the symbol name with red color
                    if len(parts) > 1:
                        self.console.insert(tk.END, parts[0] + "Symbol name : ")
                        self.console.insert(tk.END, parts[1], "red_text")
                    else:
                        self.console.insert(tk.END, line)
                
                elif "Footprint name:" in line:
                    parts = line.split("Footprint name: ")
                    if len(parts) > 1:
                        footprint_name = parts[1].strip()
                        
                    # Mark the footprint name with orange color
                    if len(parts) > 1:
                        self.console.insert(tk.END, parts[0] + "Footprint name: ")
                        self.console.insert(tk.END, parts[1], "orange_text")
                    else:
                        self.console.insert(tk.END, line)
                
                elif "3D model name:" in line:
                    parts = line.split("3D model name: ")
                    if len(parts) > 1:
                        model3d_name = parts[1].strip()
                        
                    # Mark the 3D model name with yellow color
                    if len(parts) > 1:
                        self.console.insert(tk.END, parts[0] + "3D model name: ")
                        self.console.insert(tk.END, parts[1], "yellow_text")
                    else:
                        self.console.insert(tk.END, line)
                
                else:
                    self.console.insert(tk.END, line)
                
                self.console.see(tk.END)
                self.root.update_idletasks()
            
            retcode = process.wait()
            
            if retcode == 0:
                self.status_var.set("Conversion completed successfully")
                
                # Add to history if we have component information
                if symbol_name or footprint_name or model3d_name:
                    self.add_to_history(lcsc_id, symbol_name, footprint_name, model3d_name)
            else:
                self.status_var.set("Conversion failed with code: " + str(retcode))
        
        except Exception as e:
            self.console.insert(tk.END, f"Error: {str(e)}\n")
            self.status_var.set("Conversion failed with error")
        
        finally:
            # Re-enable convert button
            self.convert_button.config(state=tk.NORMAL)
    
    def add_to_history(self, lcsc_id, symbol_name, footprint_name, model3d_name):
        # Create a dictionary with component data
        item = {
            'lcsc_id': lcsc_id,
            'symbol': symbol_name if symbol_name else "",
            'footprint': footprint_name if footprint_name else "",
            'model3d': model3d_name if model3d_name else ""
        }
        
        # Check if already exists in history
        for i, history_item in enumerate(self.history):
            if history_item['lcsc_id'] == lcsc_id:
                # Remove existing item
                self.history.pop(i)
                break
        
        # Add to beginning of history
        self.history.insert(0, item)
        
        # Limit to 250 items
        self.history = self.history[:250]
        
        # Update history display
        self.update_history_display()
        
        # Save history to file
        self.save_history()
    
    def update_history_display(self):
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Add history items to treeview
        for item in self.history:
            item_id = self.history_tree.insert("", "end", values=(
                item['lcsc_id'],
                item['symbol'],
                item['footprint'],
                item['model3d']
            ))
        
        # Add a dummy item if history is empty (should never happen now)
        if not self.history:
            self.history_tree.insert("", "end", values=(
                "C44471",
                "ACS712ELCTR-05B-T",
                "SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL",
                "SOIC-8_L4.9-W3.9-H1.7-LS6.0-P1.27"
            ))
        
        # Update the colored cells (after a slight delay to ensure the treeview is properly rendered)
        self.root.after(100, self.update_colored_cells)
    
    def update_colored_cells(self):
        """Update the colored cells by creating overlayed labels"""
        # Clear existing labels
        for label in self.colored_labels.values():
            label.destroy()
        self.colored_labels = {}
        
        # Create colored labels for each cell
        for item_id in self.history_tree.get_children():
            item = self.history_tree.item(item_id)
            values = item['values']
            
            if not values or len(values) < 4:
                continue
            
            # Get cell bounding boxes
            lcsc_id_box = self.history_tree.bbox(item_id, column=0)
            symbol_box = self.history_tree.bbox(item_id, column=1)
            footprint_box = self.history_tree.bbox(item_id, column=2)
            model3d_box = self.history_tree.bbox(item_id, column=3)
            
            if not lcsc_id_box or not symbol_box or not footprint_box or not model3d_box:
                continue  # Skip if any box is missing
                
            # Create LCSC ID label (black text)
            if values[0]:
                x, y, width, height = lcsc_id_box
                self.create_cell_label(item_id, "lcsc_id", values[0], x, y, width, height, "black")
            
            # Create symbol label (red text)
            if values[1]:
                x, y, width, height = symbol_box
                self.create_cell_label(item_id, "symbol", values[1], x, y, width, height, self.ht_red)
                
            # Create footprint label (orange text)
            if values[2]:
                x, y, width, height = footprint_box
                self.create_cell_label(item_id, "footprint", values[2], x, y, width, height, self.ht_orange)
                
            # Create 3D model label (yellow text)
            if values[3]:
                x, y, width, height = model3d_box
                self.create_cell_label(item_id, "model3d", values[3], x, y, width, height, self.ht_yellow)
    
    def create_cell_label(self, item_id, column_name, text, x, y, width, height, fg_color):
        """Create a label for a cell with proper click handling"""
        label = tk.Label(self.overlay_frame, text=text, fg=fg_color, bg="white", anchor="w", padx=5)
        label.place(x=x, y=y, width=width, height=height)
        
        # Store cell data for click handling
        label.cell_data = {
            "item_id": item_id,
            "column": column_name,
            "value": text
        }
        
        # Bind click and hover events
        label.bind("<Button-1>", self.on_cell_label_click)
        label.bind("<Enter>", lambda e, l=label: l.config(bg="#f0f0f0"))
        label.bind("<Leave>", lambda e, l=label: l.config(bg="white"))
        
        # Store the label
        self.colored_labels[f"{item_id}_{column_name}"] = label
        
        return label
    
    def on_cell_label_click(self, event):
        """Handle clicks on cell labels"""
        label = event.widget
        if hasattr(label, "cell_data"):
            # Get cell data
            cell_data = label.cell_data
            item_id = cell_data["item_id"]
            column = cell_data["column"]
            value = cell_data["value"]
            
            # Select the row
            self.history_tree.selection_set(item_id)
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(value)
            
            # Set LCSC ID if clicked on LCSC ID cell
            if column == "lcsc_id":
                self.lcsc_id_var.set(value)
                self.lcsc_id_entry.focus()
                self.status_var.set(f"LCSC ID '{value}' selected")
            else:
                # Show status for other cells
                self.status_var.set(f"{column.capitalize()} '{value}' copied to clipboard")
    
    def on_treeview_click(self, event):
        """Handle clicks directly on the treeview"""
        # Identify the clicked item and column
        region = self.history_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        # Get item ID and column
        item_id = self.history_tree.identify_row(event.y)
        column = self.history_tree.identify_column(event.x)
        
        # Get column index and name
        column_idx = int(column.replace('#', '')) - 1
        column_names = ["lcsc_id", "symbol", "footprint", "model3d"]
        if column_idx < 0 or column_idx >= len(column_names):
            return
            
        column_name = column_names[column_idx]
        
        # Get the value
        item = self.history_tree.item(item_id)
        if not item or 'values' not in item or not item['values']:
            return
            
        values = item['values']
        if column_idx >= len(values):
            return
            
        value = values[column_idx]
        if not value:
            return
            
        # Copy to clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        
        # Set LCSC ID if clicked on LCSC ID cell
        if column_name == "lcsc_id":
            self.lcsc_id_var.set(value)
            self.lcsc_id_entry.focus()
            self.status_var.set(f"LCSC ID '{value}' selected")
        else:
            # Show status for other cells
            self.status_var.set(f"{column_name.capitalize()} '{value}' copied to clipboard")
    
    def on_treeview_motion(self, event):
        """Handle mouse motion over the treeview - update cell colors when needed"""
        # Periodically update the colored cells if they don't exist
        if not self.colored_labels:
            self.update_colored_cells()
    
    def save_history(self):
        try:
            history_path = os.path.join(os.path.expanduser("~"), ".easyeda2kicad_history_simple")
            
            with open(history_path, "w") as f:
                for item in self.history:
                    f.write(f"{item['lcsc_id']}|{item['symbol']}|{item['footprint']}|{item['model3d']}\n")
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def load_history(self):
        try:
            history_path = os.path.join(os.path.expanduser("~"), ".easyeda2kicad_history_simple")
            
            if os.path.exists(history_path):
                with open(history_path, "r") as f:
                    for line in f:
                        try:
                            parts = line.strip().split("|")
                            if len(parts) >= 4:
                                self.history.append({
                                    'lcsc_id': parts[0],
                                    'symbol': parts[1],
                                    'footprint': parts[2],
                                    'model3d': parts[3]
                                })
                        except Exception:
                            # Skip problematic lines
                            continue
                
                # Limit to 250 items
                self.history = self.history[:250]
            else:
                # Add a sample entry
                self.history.append({
                    'lcsc_id': 'C44471',
                    'symbol': 'ACS712ELCTR-05B-T',
                    'footprint': 'SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL',
                    'model3d': 'SOIC-8_L4.9-W3.9-H1.7-LS6.0-P1.27'
                })
            
            # Update display
            self.update_history_display()
        except Exception as e:
            print(f"Error loading history: {e}")
            # Add a sample entry
            self.history.append({
                'lcsc_id': 'C44471',
                'symbol': 'ACS712ELCTR-05B-T',
                'footprint': 'SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL',
                'model3d': 'SOIC-8_L4.9-W3.9-H1.7-LS6.0-P1.27'
            })
            self.update_history_display()


def main():
    root = tk.Tk()
    app = EasyEda2KiCadGUI(root)
    
    # Set window icon if available
    try:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass
    
    root.mainloop()


if __name__ == "__main__":
    main()
