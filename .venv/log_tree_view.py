"""
Log Tree View — Main GUI Application
========================================

The LogTreeView class implements the primary Tkinter window for
viewing, searching, comparing, and analyzing transaction log files.

This file contains the class definition and __init__ along with
basic window/scroll/tree-navigation helpers. Domain-specific methods
are defined in the mixin modules imported below.

Author : Ergito Shkezi
Project: Master's Thesis 2026
"""

# --------------------------------------------------------------------------
# Standard Library
# --------------------------------------------------------------------------
import os
import tkinter as tk
from tkinter import messagebox, ttk

# --------------------------------------------------------------------------
# Mixin Modules (each adds a group of methods to LogTreeView)
# --------------------------------------------------------------------------
from chat_mixin import ChatMixin
from comparison_mixin import ComparisonMixin
from excel_mixin import ExcelMixin
from log_parser_mixin import LogParserMixin
from search_mixin import SearchMixin
from xml_mixin import XmlMixin


class LogTreeView(
    SearchMixin,
    ComparisonMixin,
    ExcelMixin,
    XmlMixin,
    ChatMixin,
    LogParserMixin,
    tk.Tk,
):
    """Main application window — hierarchical log viewer with integrated tools.

    Presents transaction log data in a dual-pane layout: a collapsible
    tree view (left) showing CDO/CLF depth hierarchy, and a synchronized
    text view (right) showing raw log lines with syntax colouring.
    """

    # ── GUI Initialization ──────────────────────────────────────────

    def __init__(self, log_file, file, api_key):
        super().__init__()

        self.title(f"Log Viewer - {file}")

        self.api_key = api_key
        self.log_file = log_file
        self.file = file
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        

        window_width = screen_width - 2 * 100
        window_height = screen_height - 2 * 100

 

        self.geometry(f"{window_width}x{window_height}+100+100")
        self.minsize(1600, 800)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main frame
        self.main_frame = tk.Frame(self)
        self.main_frame.grid(sticky='nsew')


        # Create PanedWindow
        self.paned_window = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.grid(row=1, column=0, sticky='nsew')
        self.paned_window_button = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window_button.grid(row=0, column=0, sticky='nsew')




        # Tree and Log frames
        self.tree_frame = tk.Frame(self.paned_window)
        self.log_frame = tk.Frame(self.paned_window)
        self.buttons =tk.Frame(self.paned_window_button)

        # Tree and Log frames
        self.tree_frame = tk.Frame(self.main_frame)
        self.tree_frame.grid(row=1, column=0, sticky='nsew')

        self.log_frame = tk.Frame(self.main_frame)
        self.log_frame.grid(row=1, column=1, sticky='nsew')

        self.buttons = tk.Frame(self.main_frame)
        self.buttons.grid(row=0, column=0, sticky='nsew')

        # Add frames to PanedWindow
        #self.paned_window.add(self.buttons)
        self.paned_window.add(self.tree_frame, minsize=0)  # Set minsize to 0 to allow complete collapse
        self.paned_window.add(self.log_frame, minsize=0)  # Set a minimum size for log frame
        self.paned_window_button.add(self.buttons) 


        # Configure tree and log frames to expand
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)



        self.tree_frame.grid_propagate(1)
        self.log_frame.grid_propagate(1)
        self.buttons.grid_propagate(1)
        
        # Button frames
        self.tree_view_frame = tk.Frame(self.tree_frame)
        self.tree_view_frame.pack(fill=tk.X)
        
        self.Buttons_position= tk.Frame(self.buttons)
        self.Buttons_position.pack(fill=tk.X)

        self.log_view_frame = tk.Frame(self.log_frame)
        self.log_view_frame.pack(fill=tk.X)

        # Create tree view columns
        for i in range(1, 6):
            setattr(self, f'tree_col{i}', tk.Frame(self.Buttons_position))
            getattr(self, f'tree_col{i}').pack(side=tk.LEFT, expand=True)

        # Tree View Components (5 columns)
        # Column 1\
        self.open_button = tk.Menubutton(self.tree_col1, text="Open", 
                                       font=("Arial", 8), bg="#6A5ACD", fg="white",
                                       relief=tk.RAISED, width=8, height=1)
        self.open_menu = tk.Menu(self.open_button, tearoff=0)
        self.open_button.config(menu=self.open_menu)
        self.open_menu.add_command(label="Open File", command=lambda: self.open_file())
        self.open_menu.add_command(label="Open Excel", command=lambda: self.open_excel())
        self.open_menu.add_command(label="Search_In_All_Files", command=lambda: self.search_in_all_files())
        self.open_menu.add_command(label="Top 5", command=lambda: self.Top_5())
        self.open_button.pack(pady=2)

        # Column 2
        self.popup_button = tk.Button(self.tree_col2, text="SiemensGPT",
                                    font=("Italic", 8), bg="#00A5A8", fg="white",
                                    command=self.open_popup, width=10, height=1)
        self.popup_button.pack(pady=2)

        # Column 3
        self.expand_all_button = tk.Button(self.tree_col3, text="Expand All",
                                         font=("Arial", 8), bg="#808000", fg="white",
                                         command=self.expand_all_nodes, width=10, height=1)
        self.expand_all_button.pack(pady=2)

        # Column 4
        self.expand_button = tk.Button(self.tree_col4, text="Expand Nodes",
                                     font=("Arial", 8), bg="#4CAF50", fg="white",
                                     command=self.expand_nodes, width=11, height=1)
        self.expand_button.pack(pady=2)

        # Column 5
        self.close_all_button = tk.Button(self.tree_col5, text="Close Nodes",
                                        font=("Arial", 8), bg="#FF7F50", fg="white",
                                        command=self.close_nodes, width=10, height=1)
        self.close_all_button.pack(pady=2)

        # Create log view columns
        for i in range(1, 5):
            setattr(self, f'log_col{i}', tk.Frame(self.Buttons_position))
            getattr(self, f'log_col{i}').pack(side=tk.LEFT, expand=True)

        # Log View Components (4 columns)
        # Column 1 (Search Entry)
        self.Search_Count = tk.Label(self.log_col1, font=("Arial", 10), text="")
        self.search_entry = tk.Entry(self.log_col1, font=("Arial", 10), width=30)
        self.search_entry.pack(side=tk.LEFT, pady=2)
        self.Search_Count.pack(side=tk.LEFT, pady=2)

        # Column 2 (Search Buttons)

        self.search_button = tk.Button(self.log_col1, text="Search",
                                     font=("Arial", 8), bg="#FFC107", fg="black",
                                     command=self.search_log, width=6, height=1)
        self.next = tk.Button(self.log_col1, text="Next",
                            font=("Arial", 8), bg="#00A5A8", fg="black",
                            command=self.next_search_result, width=6, height=1)
        self.search_button.pack(side=tk.LEFT, pady=2)
        self.next.pack(side=tk.LEFT, pady=2)

        # Column 3 (Analysis Buttons)
        self.toggle_button = tk.Button(self.log_col2, text="XML Time Processing",
                                     font=("Arial", 8), bg="White", fg="Blue",
                                     command=self.Time_Analysis_main, width=25, height=1)
        self.compare_button = tk.Button(self.log_col3, text="Compare Files",
                                      font=("Arial", 8), bg="#FF8C00", fg="white",
                                      command=lambda: self.select_file_to_compare("Main"),
                                      width=12, height=1)
        self.toggle_button.pack(side=tk.LEFT, pady=2)
        self.compare_button.pack(side=tk.LEFT, pady=2)

        # Column 4 (Chart Button)
        self.chart_ = tk.Button(self.log_col4, text="Time Chart",
                              font=("Arial", 8), bg="#4169E1", fg="white",
                              command=lambda: self.chart(), width=10, height=1)
        self.chart_.pack(pady=2)





        self.expanded_levels = 0


        columns = ("message", "delta", "CDO DeltaTime")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="tree headings")
        self.tree.tag_configure("orange_text", foreground="orange")
        self.tree.tag_configure("green_text", foreground="green")
        self.tree.heading("message", text="Message")
        self.tree.heading("delta", text="Delta Time")
        self.tree.heading("CDO DeltaTime", text="CDO DeltaTime")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.tree.configure(yscrollcommand=self.tree_scrollbar.set)

        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD)
        self.log_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.log_scrollbar = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)

        self.sync_scrollbar = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.sync_scroll_tree_log)
        self.sync_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.tree.configure(yscrollcommand=self.sync_scrollbar.set)
        self.log_text.configure(yscrollcommand=self.sync_scrollbar.set)

        self.exception_depths = []
        self.previous_timestamp = None
        self.depth_start_time = {}
        self.depth_delta_times = {}
        self.current_transaction = []
        self.log_file = log_file
        self.log_lines = []
        self.file = file
        self.highlighted_lines = []
        os.chdir(os.path.dirname(log_file))# tenngo conto della directory

        self.bind("<Control-f>", lambda event: self.search_entry.focus_set())
        self.bind("<Return>", lambda event: self.search_log())
        self.bind("<Escape>", lambda event: self.delete_search())
        self.bind("<Right>", lambda event: self.next_search_result())
        self.bind("<Left>", lambda event: self.prev_search_result())
        self.tree.bind("<Double-1>", self.highlight_log_line)
        self.bind_all('<Control-s>', lambda event: self.create_range_dialog())
                # Add scrolling functionality
        self.tree_view_frame.bind('<MouseWheel>', self.on_mousewheel_tree)
        self.log_view_frame.bind('<MouseWheel>', self.on_mousewheel_log)



        self.protocol("WM_DELETE_WINDOW", self.on_closing)


        if log_file.endswith((".txt", ".log", ".xml")):
            self.parse_log(log_file, file)
        else:
            messagebox.showerror(f"File {log_file} is not a .txt or .log file. Skipping...")

        if self.exception_depths:
            messagebox.showerror("Exception Depths:", self.exception_depths)




    def on_mousewheel_tree(self, event):
        self.tree.yview_scroll(int(-1*(event.delta/120)), "units")
        self.tree.bind('<MouseWheel>', self.on_mousewheel_tree)

    def on_mousewheel_log(self, event):
        self.log_text.yview_scroll(int(-1*(event.delta/120)), "units")
        self.log_text.bind('<MouseWheel>', self.on_mousewheel_log)

    def create_range_dialog(self):
        # Create a popup dialog
        dialog = tk.Toplevel(self)
        dialog.title("")
        
        # Remove window decorations and make it look like a search popup
        dialog.transient(self)
        dialog.resizable(False, False)
        
        # Calculate position (centered near the top of the main window)
        window_width = 400
        window_height = 40
        position_right = self.winfo_x() + (self.winfo_width() // 2) - (window_width // 2)
        position_down = self.winfo_y() + 50
        dialog.geometry(f"{window_width}x{window_height}+{position_right}+{position_down}")

        # Create a frame with raised border for search-like appearance
        frame = ttk.Frame(dialog, style='Search.TFrame')
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # From Label and Entry
        from_label = ttk.Label(frame, text="From:")
        from_label.pack(side=tk.LEFT, padx=2)
        
        # Validation command for numbers only
        vcmd = (self.register(lambda P: P == "" or P.isdigit()), '%P')
        
        # From entry
        from_entry = ttk.Entry(frame, width=10, validate='key', validatecommand=vcmd)
        from_entry.pack(side=tk.LEFT, padx=2)
        from_entry.focus_set()  # Set focus to first entry

        # To Label and Entry
        to_label = ttk.Label(frame, text="To:")
        to_label.pack(side=tk.LEFT, padx=2)

        
        
        # To entry
        to_entry = ttk.Entry(frame, width=10, validate='key', validatecommand=vcmd)
        to_entry.pack(side=tk.LEFT, padx=2)

  


        # Select button
        select_button = ttk.Button(frame, text="Select",
                                command=lambda: self.handle_range_selection(
                                    from_entry.get(), to_entry.get(), dialog))
        select_button.pack(side=tk.LEFT, padx=5)

        # Bind Enter key to select button
        dialog.bind('<Return>', lambda event: self.handle_range_selection(
            from_entry.get(), to_entry.get(), dialog))
        
        # Bind Escape key to close dialog
        dialog.bind('<Escape>', lambda event: dialog.destroy())
        
        # Bind Tab to move between entries
        from_entry.bind('<Tab>', lambda event: to_entry.focus_set())

        # Style configurations
        style = ttk.Style()
        style.configure('Search.TFrame', background='#f0f0f0')
        style.configure('TEntry', padding=3)

    def handle_range_selection(self, from_value, to_value, dialog):
        try:
            if from_value and to_value:
                from_num = int(from_value)
                to_num = int(to_value)
                selected_text=""
                if from_num <= to_num and from_num-1 >=0:
                    for i in range(from_num-1,to_num):
                        selected_text += self.log_lines[i] + "\n"

                        # Copy to clipboard
                    if selected_text:
                        self.clipboard_clear()
                        self.clipboard_append(selected_text)
                        messagebox.showinfo("Success",f"From: {from_num} To: {to_num} Text copied" )
                                # Add your logic here for what to do with the range
                    dialog.destroy()
                else:
                    messagebox.showwarning("warning","'From' value must be less than or equal to 'To' value")
            else:
                messagebox.showwarning("Warning","Please enter both values")
        except ValueError:
            messagebox.showwarning("Warning","Please enter valid numbers")

    def on_closing(self):
        """Handle window close event."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
            root.quit()

    def sync_scroll_tree_log(self,*args):
        """Synchronize scrolling between two text widgets."""
        self.tree.yview(*args)
        self.log_text.yview(*args)


    def close_nodes(self):
        """Close the current level of nodes in the tree view"""
        if self.expanded_levels > 0:
            # Get nodes at the deepest expanded level
            current_level_nodes = self.get_nodes_at_level(self.expanded_levels)
            
            # Close all nodes at the current level
            for node in current_level_nodes:
                self.tree.item(node, open=False)
            
            self.expanded_levels -= 1

    def get_nodes_at_level(self, level):
        """Helper function to get all nodes at a specific level"""
        if level == 1:
            return self.tree.get_children()
        
        nodes = []
        def collect_nodes(parent, current_level):
            if current_level == level:
                nodes.extend(self.tree.get_children(parent))
                return
            for item in self.tree.get_children(parent):
                if self.tree.item(item, "open"):
                    collect_nodes(item, current_level + 1)
        
        collect_nodes('', 1)
        return nodes



    def expand_all_nodes(self):
        """Toggle between expanding all nodes and closing all nodes"""
        if self.expanded_levels == float('inf'):
            # If all nodes are expanded, close them all
            self.recursive_close('')
            self.expanded_levels = 0
        else:
            # If not all expanded, expand all nodes
            self.recursive_expand(self.tree, '')
            self.expanded_levels = float('inf')

    def recursive_close(self, parent):
        """Recursively close all nodes in the tree view"""
        for item in self.tree.get_children(parent):
            self.tree.item(item, open=False)
            self.recursive_close(item)

    def recursive_expand(self, tree, parent):
        """Recursively expand all nodes in the tree view"""
        for item in tree.get_children(parent):
            tree.item(item, open=True)
            self.recursive_expand(tree, item)


    def expand_nodes(self):
        """Expand the next level of nodes in the tree view"""
        if self.expanded_levels == 0:
            # First level expansion
            for item in self.tree.get_children():
                self.tree.item(item, open=True)
            self.expanded_levels = 1
        else:
            # Get all nodes at the current level and expand their children
            current_level_nodes = self.get_nodes_at_level(self.expanded_levels)
            has_children = False
            
            for node in current_level_nodes:
                children = self.tree.get_children(node)
                if children:  # If the node has children
                    has_children = True
                    for child in children:
                        self.tree.item(child, open=True)
            
            if has_children:
                self.expanded_levels += 1

    def get_nodes_at_level(self, level):
        """Helper function to get all nodes at a specific level"""
        if level == 1:
            return self.tree.get_children()
        
        nodes = []
        def collect_nodes(parent, current_level):
            if current_level == level:
                nodes.extend(self.tree.get_children(parent))
                return
            for item in self.tree.get_children(parent):
                if self.tree.item(item, "open"):
                    collect_nodes(item, current_level + 1)
        
        collect_nodes('', 1)
        return nodes


    # ── File Comparison ───────────────────────────────────────

