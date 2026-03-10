"""
Log Parser Mixin — Log Parsing, Charting & Multi-File Search
===============================================================

Provides the core log parsing engine, time charting, top-5 window,
batch processing, and multi-file search functionality.

Author : Ergito Shkezi
Project: Master's Thesis 2026
"""

import os
import re
import sys
import tkinter as tk
from collections import defaultdict, deque
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, ttk

import chardet
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
from matplotlib.widgets import Button
from nltk.tokenize import word_tokenize
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QProgressDialog

from file_utils import read_lines_list_for_all, read_lines_list_XML

matplotlib.use('TkAgg')
plt.rcParams['agg.path.chunksize'] = 100000


class LogParserMixin:
    """Mixin providing log parsing, charting, and multi-file search."""

    # ── Charting & Visualization ─────────────────────────────────

    def chart(self):
        """Display a cumulative-time / derivative chart with tooltips."""

        def parse_time(t):
            try:
                dt = datetime.strptime(t, '%H:%M:%S.%f')
            except ValueError:
                dt = datetime.strptime(t, '%H:%M:%S')
            return timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)

        # Prepare data
        deltas = [parse_time(t) for t in self.delta]

        cumulative = []
        total = timedelta()
        for delta in deltas:
            total += delta
            cumulative.append(total.total_seconds() * 1000)  # milliseconds

        derivative = [cumulative[i+1] - cumulative[i] for i in range(len(cumulative)-1)]
        x_vals = list(range(1, len(cumulative) + 1))
        dx_vals = list(range(2, len(cumulative) + 1))  # derivative is between points

        # Plot setup
        fig, ax = plt.subplots()
        fig.suptitle(self.file, fontsize=16, fontweight='bold')
        plt.subplots_adjust(bottom=0.2,top=0.85)
        line, = ax.plot(x_vals, cumulative, label="Cumulative Time (ms)", marker='o')
        ax.set_xlabel("Index")
        ax.set_ylabel("Time (ms)")
        ax.set_title("Cumulative Time Plot")
        ax.grid(True)

        # Tooltip annotation
        tooltip = None
        is_derivative = [False]  # use list to allow modification in nested scope

        # Button callback
        def on_click(event):
            if line.get_label() == "Cumulative Time (ms)":
                line.set_ydata(derivative)
                line.set_xdata(dx_vals)
                line.set_label("Derivative (ms/index)")
                ax.set_ylabel("Rate of Change (ms)")
                ax.set_title("Derivative of Cumulative Time")
                is_derivative[0] = True
            else:
                line.set_ydata(cumulative)
                line.set_xdata(x_vals)
                line.set_label("Cumulative Time (ms)")
                ax.set_ylabel("Time (ms)")
                ax.set_title("Cumulative Time Plot")
                is_derivative[0] = False
            ax.relim()
            ax.autoscale_view()
            ax.legend()
            plt.draw()

        # Add button
        ax_button = plt.axes([0.7, 0.05, 0.2, 0.075])
        button = Button(ax_button, 'Toggle Derivative', color='orange', hovercolor='darkorange')
        button.on_clicked(on_click)

        # Right-click handler
        def on_right_click(event):
            nonlocal tooltip

            if event.button != MouseButton.RIGHT or event.inaxes != ax:
                return

            x_data = dx_vals if is_derivative[0] else x_vals
            y_data = derivative if is_derivative[0] else cumulative

            if event.xdata is None or event.ydata is None:
                return

            # Find closest point
            distances = [(abs(event.xdata - x), abs(event.ydata - y)) for x, y in zip(x_data, y_data)]
            closest_index = min(range(len(distances)), key=lambda i: distances[i][0] + distances[i][1])
            actual_index = x_data[closest_index] - 1  # account for 1-based x_vals

            if actual_index < 0 or actual_index >= len(self.log_lines):
                return

            # Remove existing tooltip
            if tooltip:
                tooltip.remove()

            # Add new tooltip
            tooltip = ax.annotate(
                self.log_lines[actual_index],
                xy=(x_data[closest_index], y_data[closest_index]),
                xytext=(15, 15),
                textcoords='offset points',
                bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.9),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
            )
            self.highlight_log_line_by_index(actual_index)
            plt.draw()

        # Connect mouse event
        fig.canvas.mpl_connect('button_press_event', on_right_click)

        plt.show()




    def highlight_log_line_by_index(self, index):
        try:
            # Check if line number is valid
            if 0 <= index < len(self.log_lines):
                # Instead of reinserting all text, just add highlight tag
                start = f"{index + 1}.0"
                end = f"{index + 1}.end"
                self.log_text.tag_add("highlight", start, end)
                self.log_text.see(start)
            else:
                messagebox.showerror("Error", f"Invalid line number: {index}")
        except Exception as e:
            messagebox.showerror("Error", f"Error in highlighting: {e}")


    # ── Multi-File Search ──────────────────────────────────────

    def Show_All_Matches(self, path):
        """Open a tree-view window showing search results across all files in *path*."""
        try:
            # Create main window
            tree_window = tk.Toplevel(self)
            tree_window.title("Find")
            tree_window.geometry("1400x800")

            # Create main frame
            main_frame = ttk.Frame(tree_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Create search frame
            search_frame = ttk.Frame(main_frame)
            search_frame.pack(fill=tk.X, pady=(0, 10))

            search_label = ttk.Label(search_frame, text="Search Content:")
            search_label.pack(side=tk.LEFT, padx=(0, 5))

            search_entry = ttk.Entry(search_frame)
            search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Create tree frame
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            # Create Treeview
            tree = ttk.Treeview(tree_frame)
            
            # Add scrollbars
            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            # Layout management
            tree.grid(column=0, row=0, sticky='nsew')
            vsb.grid(column=1, row=0, sticky='ns')
            hsb.grid(column=0, row=1, sticky='ew')
            tree_frame.grid_columnconfigure(0, weight=1)
            tree_frame.grid_rowconfigure(0, weight=1)

            # Configure tree columns
            tree["columns"] = ("content",)
            tree.column("#0", width=200, stretch=tk.YES)
            tree.column("content", width=1000, stretch=tk.YES)
            tree.heading("#0", text="Filename")
            tree.heading("content", text="Found Rows")

            self.Directory_of_all_file_search=path

            def update_tree_content():
                """Update the treeview with search results"""
                try:
                    # Clear existing items
                    for item in tree.get_children():
                        tree.delete(item)

                    # Insert new items
                    for filename, matching_lines in self.lines_found.items():
                        parent = tree.insert("", "end", text=filename, values=("",))
                        
                        # Insert child nodes (matching lines)
                        for line in (matching_lines):
                            tree.insert(parent, "end", text=f"=", values=(f"{line}",))
                        
                        # Expand parent node
                        tree.item(parent, open=True)
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            def on_double_click(event):
                """Handle double-click events on tree items"""
                try:
                    item = tree.identify('item', event.x, event.y)
                    if item and not tree.parent(item):  # If it's a parent node
                        if tree.item(item, 'open'):
                            tree.item(item, open=False)
                        else:
                            tree.item(item, open=True)
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            def local_start_search(search_term):
                """Local function to handle search and update tree"""
                self.start_search_all(path, search_term)
                update_tree_content()

            # Add search button with local search function
            search_button = ttk.Button(
                search_frame, 
                text="Search", 
                command=lambda: local_start_search(search_entry.get())
            )
            search_button.pack(side=tk.LEFT, padx=(5, 0))

            # Bind events
            search_entry.bind("<Return>", 
                            lambda event: local_start_search(search_entry.get()))
            tree.bind("<Control-f>", lambda event: search_entry.focus_set())
            tree.bind("<Double-1>", on_double_click)
            tree.bind("<Button-3>", lambda event:self.show_sql_popup_all_files(tree,event))

            # Update tree if results exist
            if hasattr(self, 'lines_found') and self.lines_found:
                update_tree_content()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_search_all(self, path, search_term):
        """Start the search process in all files"""
        try:
            self.lines_found = {}
            if not search_term:
                messagebox.showwarning("Warning", "Please enter a search term")
                return

            for file in os.listdir(path):
                if file.endswith((".txt", ".log")):
                    file_path = os.path.join(path, file)
                    self.lines_found[file] = read_lines_list_for_all(file_path, search_term)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def Top_5(self):
        self.top_5_window()

    def search_in_all_files(self):
        """Open folder selector and initiate search"""
        try:
            path = filedialog.askdirectory(title="Select Folder")
            if path:  # Proceed only if a directory was selected
                path = path.strip()
                self.Show_All_Matches(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def show_sql_popup_all_files(self, tree, event):  # Change coordinates to event
        # Get item at coordinates
        item = tree.identify_row(event.y)
        if item:
            # Get values from the item
            values = tree.item(item)['values']
            if values and len(values) > 0:
                    f = values[0]  # Get SQL text from third column
            if tree.item(item)['text']:
                l=tree.item(item)['text']



            # Create popup window
            popup = tk.Toplevel(self)
            popup.title("Text Values")
            popup.geometry("800x400")
            text_widget = tk.Text(popup, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True)
            
            # Add scrollbars
            vsb = ttk.Scrollbar(popup, orient="vertical", command=text_widget.yview)
            hsb = ttk.Scrollbar(popup, orient="horizontal", command=text_widget.xview)
            text_widget.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            
            vsb.pack(side=tk.RIGHT, fill=tk.Y)
            hsb.pack(side=tk.BOTTOM, fill=tk.X)
            if f:
                text_widget.insert(tk.END, f)
            elif l:
                #text_widget.insert(tk.END, l)
                popup.destroy()  # Close the current popup window
                from log_tree_view import LogTreeView
                log_tree_view=LogTreeView(f"{self.Directory_of_all_file_search}/{l}", l, self.api_key)
                log_tree_view.mainloop() 

            text_widget.config(state='disabled')  # Make it read-only

    def parse_log(self, log_file, file):
        """Parse the log file, build the tree hierarchy, and populate the UI."""
        # Pre-compile patterns
        TIMESTAMP_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})")
        TIMESTAMP_AND_TOKEN_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+")
        DEPTH_PATTERN = re.compile(r"Depth: (\d+)")
        LEAVING_PATTERN = re.compile(r"Leaving Depth")
        
        # Use deque for better performance with stack operations
        stack = deque()
        parent_map = {}
        node_values = {}  # Store node values in memory
        self.refference=["0000-00-00 00:00:00.000000"]*5
        self.ref_line=[""]*5
        self.delta=[]
        # Initialize QApplication if needed
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        # Create and configure progress dialog
        progress = QProgressDialog(
            "Processing log lines...",
            "Cancel",
            0,
            100,
            None,
            Qt.WindowType.WindowStaysOnTopHint
        )
        progress.setWindowTitle("Progress")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0) 
        progress.show()
        QApplication.processEvents()
        
        try:
            # Get log lines
            self.response, self.log_lines = read_lines_list_XML(log_file)
            total_lines = len(self.log_lines)
            progress.setMaximum(total_lines)
            
            # Initialize processing variables
            self.start_async_processing()
            self.previous_timestamp = None
            self.depth_start_time = defaultdict(datetime.now)
            self.depth_delta_times = defaultdict(datetime.now)
            self.current_transaction = []
            
            # Process lines with batch updates
            batch_size = 1000
            current_batch = []
            
            for index, line in enumerate(self.log_lines):
                if progress.wasCanceled():
                    break
                    
                # Process timestamp
                timestamp_match = TIMESTAMP_PATTERN.match(line)
                delta = ""
                cdo_delta = ""
                
                if timestamp_match:
                    current_timestamp = timestamp_match.group(1)
                    curr_dt = datetime.strptime(current_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    if self.previous_timestamp:
                        prev_dt = datetime.strptime(self.previous_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                        delta = str(curr_dt - prev_dt)
                        if len(delta) >= 14:
                            delta = delta[:len(delta) - 3]
                        if delta > self.refference[0]:
                            self.refference[0]=delta
                            self.ref_line[0]=line
                        elif delta > self.refference[1]:
                            self.refference[1]=delta
                            self.ref_line[1]=line
                        elif delta > self.refference[2]:
                            self.refference[2]=delta
                            self.ref_line[2]=line
                        elif delta > self.refference[3]:
                            self.refference[3]=delta
                            self.ref_line[3]=line
                        elif delta > self.refference[4]:
                            self.refference[4]=delta
                            self.ref_line[4]=line
                        self.delta.append(delta)
                    self.previous_timestamp = current_timestamp
                else:
                    #current_timestamp = timestamp_match.group(1)
                    curr_dt = prev_dt
                    prev_dt = datetime.strptime(self.previous_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    delta = str(curr_dt - prev_dt) #28/05
                    self.delta.append(delta)    #
                    self.previous_timestamp = current_timestamp#
                
                # Extract message
                message = TIMESTAMP_AND_TOKEN_PATTERN.sub("", line)
                display_message = f"{index + 1}:    " + message.strip()
                
                # Handle exceptions
                if "EXCEPTION" in line:
                    error = self.log_lines[index + 3]
                    self.after(0, lambda: tk.messagebox.showwarning(
                        "Warning", 
                        f"Exception found in file: {file}-> \n{error}"
                    ))
                
                # Handle transactions
                elif "starting transaction" in line:
                    self.current_transaction = [display_message]
                elif self.current_transaction:
                    self.current_transaction.append(display_message)
                
                # Process depth information
                depth_match = DEPTH_PATTERN.search(line)
                leaving_match = LEAVING_PATTERN.search(line)
                
                if leaving_match:
                    # Create node for leaving entry regardless of stack state
                    parent = stack[-1] if stack else ""  # If stack is empty, parent will be ""
                    node_id = f"node_{index}"
                    node_values[node_id] = (display_message, delta, "")
                    current_batch.append(('insert', parent, "end", node_id, {
                        'values': (display_message, delta, ""),
                        'tags': ("orange_text",)
                    }))

                    # Handle stack updates if stack is not empty
                    if stack:
                        parent_id = stack[-1]
                        depth = len(stack) - 1
                        if depth in self.depth_start_time:
                            cdo_delta = str(curr_dt - self.depth_start_time[depth])
                            if parent_id in node_values:
                                values = node_values[parent_id]
                                current_batch.append(('item_update', parent_id, {
                                    'values': (values[0], values[1], cdo_delta),
                                    'tags': ("orange_text",)
                                }))
                
                elif depth_match:
                    depth = int(depth_match.group(1))
                    self.depth_start_time[depth] = curr_dt
                    
                    # Update stack
                    while len(stack) > depth:
                        popped_node = stack.pop()
                        if popped_node in self.depth_delta_times:
                            cdo_delta = str(curr_dt - self.depth_delta_times[popped_node])
                            if len(cdo_delta) >= 14:
                                cdo_delta = cdo_delta[:len(cdo_delta) - 3]
                            if popped_node in node_values:
                                values = node_values[popped_node]
                                current_batch.append(('item_update', popped_node, {
                                    'values': (values[0], values[1], cdo_delta),
                                    'tags': ("green_text",)
                                }))
                    
                    # Create new node
                    parent = stack[-1] if stack else ""
                    node_id = f"node_{index}"
                    node_values[node_id] = (display_message, delta, "")
                    current_batch.append(('insert', parent, "end", node_id, {
                        'values': (display_message, delta, ""),
                        'tags': ("green_text",)
                    }))
                    
                    stack.append(node_id)
                    parent_map[depth] = node_id
                    self.depth_delta_times[node_id] = curr_dt
                 
                
                else:
                    if self.current_transaction:
                        parent = stack[-1] if stack else ""
                        node_id = f"trans_{index}"
                        node_values[node_id] = (display_message, delta, "")
                        current_batch.append(('insert', parent, "end", node_id, {
                            'values': (display_message, delta, ""),
                            'tags': (f"line_{index}",)
                        }))
                
                # Batch processing
                if len(current_batch) >= batch_size:
                    self._process_batch(current_batch)
                    current_batch = []
                
                # Update progress
                progress.setValue(index + 1)
                QApplication.processEvents()
                
                # Periodic UI updates
                if index % batch_size == 0:
                    self.update_idletasks()
            
            # Process remaining batch items
            if current_batch:
                self._process_batch(current_batch)
            
            # Update text area efficiently
            self._update_text_area()
            
        finally:
            progress.close()
            if 'app' in locals():
                app.quit()
        

    def top_5_window(self):
        popup = tk.Toplevel()
        popup.title(f"Line Refference of {self.file}")
        popup.geometry("800x400")
        text_widget = tk.Text(popup, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(popup, orient="vertical", command=text_widget.yview)
        hsb = ttk.Scrollbar(popup, orient="horizontal", command=text_widget.xview)
        text_widget.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        for j in range(0,5):

            text_widget.insert(tk.END, f"{self.ref_line[j]} \n time: {self.refference[j]}\n\n" )
    
    
        text_widget.config(state='disabled')  # Make it read-only


    def _process_batch(self, batch):
        """Helper method to process batch updates to the tree"""
        try:
            for operation in batch:
                if operation[0] == 'insert':
                    _, parent, position, node_id, properties = operation
                    self.tree.insert(parent, position, iid=node_id, **properties)
                elif operation[0] == 'item_update':
                    _, node_id, properties = operation
                    try:
                        self.tree.item(node_id, **properties)
                    except tk.TclError:
                        pass  # Skip if item not found
        except Exception as e:
            messagebox.showinfo("Error", f"Error processing batch: {str(e)}")


    def _update_text_area(self):
        """Helper method to efficiently update the text area"""
        try:
            self.log_text.config(state="normal")
            self.log_text.delete("1.0", tk.END)

            self.log_lines_compare = self.log_lines 

            # ✅ Update self.log_lines here (adding line numbers once)
            self.log_lines = [f"{i + 1}: {line}" for i, line in enumerate(self.log_lines)]

            # Configure tags only once
            tag_configs = {
                "line_number": {"foreground": "purple"},
                "depth_entry": {"foreground": "green"},
                "leaving_depth": {"foreground": "#FF8000"},
                "highlight": {"background": "yellow"},
            }
            for tag, options in tag_configs.items():
                self.log_text.tag_configure(tag, **options)

            # Insert all text at once
            insert_text = "\n".join(self.log_lines) + "\n"
            self.log_text.insert(tk.END, insert_text)

            # Now tag line numbers and entries
            for i, line in enumerate(self.log_lines):
                line_start = f"{i + 1}.0"
                line_num_len = len(f"{i + 1}: ")
                num_end = f"{i + 1}.{line_num_len}"

                self.log_text.tag_add("line_number", line_start, num_end)

                content_start = f"{i + 1}.{line_num_len}"

                if "Depth:" in line and "Leaving" not in line:
                    self.log_text.tag_add("depth_entry", content_start, f"{i + 1}.end")
                elif "Leaving Depth:" in line:
                    self.log_text.tag_add("leaving_depth", content_start, f"{i + 1}.end")

            self.log_text.see("1.0")
            self.log_text.config(state="disabled")  # Optional: make readonly

        except Exception as e:
            messagebox.showinfo("Error", f"Error updating text area: {str(e)}")



