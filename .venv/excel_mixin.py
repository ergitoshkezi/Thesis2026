"""
Excel Mixin — Excel Data Viewer & Sorting
=============================================

Provides methods for loading, displaying, sorting, and
navigating Excel overview files within LogTreeView.

Author : Ergito Shkezi
Project: Master's Thesis 2026
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd
import Structure_Excel


class ExcelMixin:
    """Mixin providing Excel viewer functionality."""

    def read_Excel(self, filename):
        """Load an Excel file into a DataFrame and display it."""
        try:
            # Read the Excel file
            self.df = pd.read_excel(filename)
            self.show_excel_data()
            return self.df
        except Exception as e:
            messagebox.showerror("Error", f"Error reading the file: {str(e)}")
            return None
    
    def show_excel_data(self):
        excel_window = tk.Toplevel(self)
        excel_window.title("Excel Data Viewer")
        excel_window.geometry("800x600")
        
        main_frame = ttk.Frame(excel_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame)
        y_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        x_scrollbar = ttk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        
        data_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)
        
        canvas.create_window((0, 0), window=data_frame, anchor="nw")
        
        # Calculate maximum width for each column
        max_widths = {}
        for col_idx, column in enumerate(self.df.columns):
            # Get maximum width from column name and data
            column_values = self.df[column].astype(str)
            max_width = max(
                len(str(column)),  # Header length
                column_values.str.len().max()  # Maximum data length
            )
            # Set a minimum width of 10 and maximum of 50 characters
            max_widths[col_idx] = min(max(max_width, 10), 50)

        # Create header labels with calculated widths
        for col_idx, column in enumerate(self.df.columns):
            header_label = ttk.Label(data_frame, 
                                text=column, 
                                font=('Arial', 10, 'bold'),
                                background='#e0e0e0', 
                                relief='raised', 
                                padding=5,
                                width=max_widths[col_idx])  # Set width here
            header_label.grid(row=0, column=col_idx, sticky='nsew')
            
            # Configure column weight
            data_frame.grid_columnconfigure(col_idx, weight=1, minsize=max_widths[col_idx]*8)
        
        # Create Entry widgets for each cell with calculated widths
        for row_idx, row in enumerate(self.df.values):
            first_col_value = str(row[0])  # Get first column value
            for col_idx, value in enumerate(row):
                entry = tk.Entry(data_frame, 
                            readonlybackground='white', 
                            justify='left',
                            width=max_widths[col_idx])  # Set width here
                entry.insert(0, str(value))
                entry.configure(state='readonly', relief='flat')
                entry.grid(row=row_idx+1, column=col_idx, sticky='nsew', padx=1, pady=1)
                entry.bind('<Button-3>', 
            lambda event, first_val=first_col_value: 
            self.open_file_from_excel(Structure_Excel.path, first_val))
                
                def select_all(event):
                    event.widget.configure(state='normal')
                    event.widget.select_range(0, tk.END)
                    event.widget.configure(state='readonly')
                
                entry.bind('<Button-1>', select_all)

        # Update scroll region
        data_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        button_frame = ttk.Frame(excel_window)
        button_frame.pack(pady=10)
        
        # Add sorting buttons
        sort_frame = ttk.LabelFrame(button_frame, text="Sort by")
        sort_frame.pack(side=tk.LEFT, padx=10)

        # Duration of TXN sorting
        duration_sort_asc = ttk.Button(sort_frame, 
                                    text="Duration ↑", 
                                    command=lambda: [self.sort_dataframe("Duration of TXN", True), 
                                                    self.refresh_excel_data(data_frame)])
        duration_sort_asc.pack(side=tk.LEFT, padx=2)

        duration_sort_desc = ttk.Button(sort_frame, 
                                    text="Duration ↓", 
                                    command=lambda: [self.sort_dataframe("Duration of TXN", False), 
                                                    self.refresh_excel_data(data_frame)])
        duration_sort_desc.pack(side=tk.LEFT, padx=2)

        # Biggest Gap sorting
        gap_sort_asc = ttk.Button(sort_frame, 
                                text="Gap ↑", 
                                command=lambda: [self.sort_dataframe("Biggest Gap", True), 
                                            self.refresh_excel_data(data_frame)])
        gap_sort_asc.pack(side=tk.LEFT, padx=2)

        gap_sort_desc = ttk.Button(sort_frame, 
                                text="Gap ↓", 
                                command=lambda: [self.sort_dataframe("Biggest Gap", False), 
                                                self.refresh_excel_data(data_frame)])
        gap_sort_desc.pack(side=tk.LEFT, padx=2)

        # Combined sorting
        combined_sort_asc = ttk.Button(sort_frame, 
                                    text="Duration & Gap ↑", 
                                    command=lambda: [self.sort_dataframe(
                                        ["Duration of TXN", "Biggest Gap"], 
                                        [True, True]), 
                                        self.refresh_excel_data(data_frame)])
        combined_sort_asc.pack(side=tk.LEFT, padx=2)

        combined_sort_desc = ttk.Button(sort_frame, 
                                    text="Duration & Gap ↓", 
                                    command=lambda: [self.sort_dataframe(
                                        ["Duration of TXN", "Biggest Gap"], 
                                        [False, False]), 
                                        self.refresh_excel_data(data_frame)])
        combined_sort_desc.pack(side=tk.LEFT, padx=2)
        
        close_button = ttk.Button(button_frame, 
                                text="Close", 
                                command=excel_window.destroy)
        close_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = ttk.Button(button_frame, 
                                text="Refresh", 
                                command=lambda: self.refresh_excel_data(data_frame))
        refresh_button.pack(side=tk.LEFT, padx=5)

    def refresh_excel_data(self, frame):
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Calculate maximum width for each column
        max_widths = {}
        for col_idx, column in enumerate(self.df.columns):
            column_values = self.df[column].astype(str)
            max_width = max(
                len(str(column)),
                column_values.str.len().max()
            )
            max_widths[col_idx] = min(max(max_width, 10), 50)

        # Recreate headers with calculated widths
        for col_idx, column in enumerate(self.df.columns):
            header_label = ttk.Label(frame, 
                                text=column, 
                                font=('Arial', 10, 'bold'),
                                background='#e0e0e0', 
                                relief='raised', 
                                padding=5,
                                width=max_widths[col_idx])
            header_label.grid(row=0, column=col_idx, sticky='nsew')
            
            # Configure column weight
            frame.grid_columnconfigure(col_idx, weight=1, minsize=max_widths[col_idx]*8)
        
        # Recreate Entry widgets with calculated widths
        for row_idx, row in enumerate(self.df.values):
            first_col_value = str(row[0])  # Get first column value
            for col_idx, value in enumerate(row):
                entry = tk.Entry(frame, 
                            readonlybackground='white', 
                            justify='left',
                            width=max_widths[col_idx])
                entry.insert(0, str(value))
                entry.configure(state='readonly', relief='flat')
                entry.grid(row=row_idx+1, column=col_idx, sticky='nsew', padx=1, pady=1)
                entry.bind('<Button-3>', 
                        lambda event, first_val=first_col_value: 
                        self.open_file_from_excel(Structure_Excel.path, first_val))
                
                def select_all(event):
                    event.widget.configure(state='normal')
                    event.widget.select_range(0, tk.END)
                    event.widget.configure(state='readonly')
                
                entry.bind('<Button-1>', select_all)

    def sort_dataframe(self, columns, ascending=True):
        """
        Sort the dataframe by the specified column(s)
        columns can be a single column name or a list of column names
        ascending can be a single boolean or a list of booleans
        """
        try:
            # Convert duration and gap columns to numeric, removing any non-numeric characters
            if isinstance(columns, str):
                columns = [columns]
            
            # Create temporary columns for sorting
            for col in columns:
                if col in ["Duration of TXN", "Biggest Gap"]:
                    # Create a temporary column for sorting
                    temp_col = f"{col}_temp"
                    # Convert to string first to ensure .str accessor works
                    self.df[temp_col] = self.df[col].astype(str)
                    # Extract numeric values
                    self.df[temp_col] = pd.to_numeric(
                        self.df[temp_col].str.replace(r'[^\d.]', '', regex=True),
                        errors='coerce'
                    )
                    
            # Replace original columns in the sorting list with temporary columns
            sort_columns = [f"{col}_temp" if col in ["Duration of TXN", "Biggest Gap"] else col 
                        for col in columns]
            
            # Perform the sort
            self.df = self.df.sort_values(by=sort_columns, ascending=ascending)
            
            # Remove temporary columns
            for col in columns:
                if col in ["Duration of TXN", "Biggest Gap"]:
                    temp_col = f"{col}_temp"
                    if temp_col in self.df.columns:
                        self.df = self.df.drop(columns=[temp_col])
                        
        except Exception as e:
            messagebox.showerror("Sorting Error", f"Error while sorting: {str(e)}")




    def open_file_from_excel(self,path,name):
        from log_tree_view import LogTreeView
        log_tree_view=LogTreeView(path+'/'+name, name, self.api_key)
        log_tree_view.mainloop() 



    def open_file(self):
        from log_tree_view import LogTreeView
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            #new_log_tree_view = LogTreeView(file_path, file_name)  # Create a new instance for the new file
            log_tree_view=LogTreeView(file_path, file_name, self.api_key)
            log_tree_view.mainloop() 


    def call(self):
        try:
        # Run the main function from Structure_Excel.py
            Structure_Excel.main()
            self.read_Excel("_Overview.xlsx")
        except Exception as e:
            messagebox.showerror(f"Error occurred: {e}")


    
    def open_excel(self):
        #self.start_async_processing_()
        self.call()
    # ── Window & Scroll Management ───────────────────────────────

