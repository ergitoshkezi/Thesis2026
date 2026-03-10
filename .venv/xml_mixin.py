"""
XML Mixin — XML Analysis & Tree Viewers
==========================================

Provides methods for XML timing analysis, tree-view display
of XML structure, and XML file generation.

Author : Ergito Shkezi
Project: Master's Thesis 2026
"""

import asyncio
import json
import os
import threading
import tkinter as tk
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, ttk

from lxml import etree
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QProgressDialog

from file_utils import read_lines_list_XML


class XmlMixin:
    """Mixin providing XML analysis and tree-viewer functionality."""

    def show_Result_popup(self, query_data):
        root = tk.Toplevel()
        root.title(f"Hierarchical Query Analysis of {self.file}")
        root.geometry("1400x900")

        # Create main frame with specific padding
        main_frame = tk.Frame(root, padx=40, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Calculate the desired canvas width (70% of window width)
        canvas_width = int(1400 * 0.70)  # 980 pixels

        # Create scrollable canvas with specific dimensions
        canvas = tk.Canvas(
            main_frame, 
            width=canvas_width,
            height=800,  # Fixed height, adjust if needed
            highlightthickness=0  # Removes border
        )
        scrollbar = tk.Scrollbar(main_frame, command=canvas.yview, width=16)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        # Configure grid weights for perfect centering
        main_frame.grid_columnconfigure(0, weight=1)  # Left margin
        main_frame.grid_columnconfigure(1, weight=0)  # Canvas column (fixed width)
        main_frame.grid_columnconfigure(2, weight=0)  # Scrollbar column
        main_frame.grid_columnconfigure(3, weight=1)  # Right margin
        main_frame.grid_rowconfigure(0, weight=1)

        # Place canvas and scrollbar
        canvas.grid(row=0, column=1, sticky='ns')
        scrollbar.grid(row=0, column=2, sticky='ns')

        # Create inner frame with specific width
        inner_frame = tk.Frame(canvas, width=canvas_width)
        canvas.create_window(
            (canvas_width//2, 0),  # Center horizontally
            window=inner_frame, 
            anchor='n',  # Top center anchor
            width=canvas_width  # Fix the width
        )

        # Make sure the inner frame maintains its width
        inner_frame.grid_propagate(False)

        def format_time_delta(delta_time_ms):
            """Convert milliseconds to a readable format"""
            seconds = delta_time_ms / 1000
            if seconds < 1:
                return f"{delta_time_ms:.2f}ms"
            elif seconds < 60:
                return f"{seconds:.2f}s"
            else:
                minutes = int(seconds // 60)
                remaining_seconds = seconds % 60
                return f"{minutes}m {remaining_seconds:.2f}s"

        def create_node_display(parent, node_data, level=0):
            """Recursively create display for node and its subnodes"""
            frame = tk.Frame(parent, relief=tk.GROOVE, borderwidth=1)
            frame.pack(fill=tk.X, pady=2, padx=level*10)
                # Create a header frame to contain both the label and button
            header_frame = tk.Frame(frame)
            header_frame.pack(fill=tk.X, padx=5, pady=2)

            # Create header with node type and timing
            header_text = f"{'  ' * level}► {node_data['node_type']}"
            if 'delta_time_ms' in node_data and  '__query' in node_data['node_type'].lower():
                header_text += f" (Time: {format_time_delta(node_data['delta_time_ms'])}"
                if 'percentage_of_total' in node_data:
                    header_text += f", {node_data['percentage_of_total']:.2f}%"
                header_text += ")"

            header = tk.Label(header_frame, text=header_text, anchor='w', justify=tk.LEFT)
            header.pack(side=tk.LEFT, fill=tk.X, expand=True)

            def get_sql_text(node_data):
                """Extract SQL text from node data"""
                if '__query' in node_data['node_type'].lower():
                    
                    # First try to find SQL text in subnodes
                    for subnode in node_data.get('subnodes', []):
                        if subnode['node_type'] == '__parsedSQLText' and 'text' in subnode:
                            return subnode['text']
                        elif subnode['node_type'] == '__rawSQLText' and 'text' in subnode:
                            return subnode['text']
                    
                    # If not found in subnodes, check attributes
                    attributes = node_data.get('attributes', {})
                    if 'rawSQLText' in attributes:
                        return attributes['rawSQLText']
                    elif 'parsedSQLText' in attributes:
                        return attributes['parsedSQLText']
                return None

            def on_find_query():
                sql_text = get_sql_text(node_data)
                if sql_text:
                        self.clipboard_clear()
                        self.clipboard_append(sql_text)
                else:
                    print("No SQL query found in this node.")

            # Only show the Find Query button if this node might contain a query
            if '__query' in node_data['node_type'].lower() and  node_data['node_type'] not in ['__parsedSQLText', '__rawSQLText','__queryParameter','__queryParameters']: 
                find_button = tk.Button(
                    header_frame,
                    text="Copy Query",
                    command=on_find_query,
                    relief=tk.GROOVE,
                    background="Green",
                    padx=5,
                    pady=2,
                    font=('Arial', 8)
                )
                find_button.pack(side=tk.RIGHT, padx=(5, 0))

            # Create collapsible content section
            content_frame = tk.Frame(frame)
            content_frame.pack(fill=tk.X, padx=5, pady=2)


            # Display node text if it exists
            if 'text' in node_data:
                # Determine the height based on node type
                text_height = 15 if node_data['node_type'] in ['__parsedSQLText', '__rawSQLText'] else 5
                
                # Create a frame to hold the Text widget and scrollbar
                text_frame = tk.Frame(content_frame)
                text_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

                # Create a Text widget for the node text with adjusted height
                node_text_widget = tk.Text(text_frame, 
                                        wrap='word', 
                                        height=text_height,  # Using the dynamic height
                                        font=('Courier New', 10))

                # Create and configure scrollbar
                scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=node_text_widget.yview)
                node_text_widget.configure(yscrollcommand=scrollbar.set)

                # Pack the Text widget and scrollbar
                node_text_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                # Insert the node text
                node_text_widget.insert(tk.END, f"{node_data['text']}")
                node_text_widget.config(state=tk.DISABLED)  # Make the Text widget read-only


            # Display attributes if they exist
            if 'attributes' in node_data:
                attr_text = "Attributes:\n" + "\n".join(f"{k}: {v}" 
                        for k, v in node_data['attributes'].items())
                attr_label = tk.Label(content_frame, 
                                    text=attr_text, 
                                    wraplength=800, 
                                    justify=tk.LEFT)
                attr_label.pack(fill=tk.X)

            # Recursively display subnodes
            if 'subnodes' in node_data and node_data['subnodes']:
                subnodes_frame = tk.Frame(frame)
                subnodes_frame.pack(fill=tk.X, pady=2)
                
                for subnode in node_data['subnodes']:
                    create_node_display(subnodes_frame, subnode, level + 1)
   

        # Display header with total statistics and warning if needed
        total_queries = len(query_data)
        displayed_queries = min(total_queries, 40)
        
        header_text = []
        if query_data:
            total_time_ms = sum((q.get('delta_time_ms', 0) for q in query_data))
            header_text.append(f"Total Analysis Time: {format_time_delta(total_time_ms)}")
            header_text.append(f"Total Queries Found: {total_queries}")
            
            if total_queries > 40:
                header_text.append(f"Displaying top 40 most time-consuming queries")
                header_text.append(f"({total_queries - 40} queries hidden)")
                
                # Add warning in red
                warning_label = tk.Label(inner_frame, 
                                    text="⚠️ Large number of queries detected - showing top 40 only",
                                    fg='red',
                                    font=('Arial', 11, 'bold'))
                warning_label.pack(pady=(5,0))

        header_label = tk.Label(inner_frame, 
                            text="\n".join(header_text), 
                            font=('Arial', 12, 'bold'))
        header_label.pack(pady=10)

        # Display limited number of queries
        real_query_count = 0

        for i,query in enumerate(query_data[:displayed_queries], 1):
            if query['node_type'] not in ['__parsedSQLText', '__rawSQLText','__queryParameter','__queryParameters']: 
                real_query_count+=1
                query_frame = tk.Frame(inner_frame, relief=tk.RAISED, borderwidth=2)
                query_frame.pack(fill=tk.X, pady=5)
                
                # Add query number to the display
                number_label = tk.Label(query_frame, 
                                    text=f"Query #{real_query_count}", 
                                    font=('Arial', 11, 'bold'))
                number_label.pack(anchor='w', padx=5, pady=(5,0))
                
                create_node_display(query_frame, query)

        # Add scrolling functionality
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        root.bind('<Up>', lambda e: canvas.yview_scroll(-1, "units"))
        root.bind('<Down>', lambda e: canvas.yview_scroll(1, "units"))




    def Time_Analysis(self):

            self.file_chosen = filedialog.askopenfilename(title="Select XML file to Analyze")
            if self.file_chosen:

                if self.file_chosen.endswith('.xml'):
                    self.only_show_XML_TreeView(self.file_chosen)
                else:
                    self.show_XML_TreeView(self.file_chosen)


    def Time_Analysis_main(self):
        # First try to load the JSON file
        json_file = f"{self.file.split('.')[0]}_tree_analysis.json"
        xml_file = f"{self.file.split('.')[0]}.xml"
        
        os.chdir(self.log_file.split(f'{self.file}')[0])#position in the folder of the chosen log file, cause at ht begining it is modified by a opened new file
        if  os.path.isdir(self.file.split('.')[0]):
            os.chdir(self.file.split('.')[0])
        if os.path.exists(json_file):
            self.show_XML_TreeView(json_file)
            
        elif os.path.exists(xml_file):
            self.only_show_XML_TreeView(xml_file)
            
        else:
            self.file_chosen = filedialog.askopenfilename(
                title="Select XML file to Analyze",
                filetypes=[
                    ("XML files", "*.json"),
                    ("JSON files", "*.xml"),
                    ("All files", "*.*")
                ]
            )
            
            if self.file_chosen:
                if self.file_chosen.endswith('.xml'):
                    self.only_show_XML_TreeView(self.file_chosen)
                else:
                    self.show_XML_TreeView(self.file_chosen)
            else:
                messagebox.showerror("No Json or Xml Found ")


    # ── XML Analysis ───────────────────────────────────────────

    def Analyze_XML(self, file_xml):
        """Parse an XML file and extract query timing data, sorted by duration."""
        try:
            tree = etree.parse(file_xml)
           
            root = tree.getroot()
            all_query_data = []

            def get_timing_info(node):
                """Extract timing information from a node"""
                start_time_elem = node.find('./__startTime')
                end_time_elem = node.find('./__endTime')
                
                if start_time_elem is not None and end_time_elem is not None:
                    try:
                        start_time_str = start_time_elem.text.strip()
                        end_time_str = end_time_elem.text.strip()
                        
                        start_time = datetime.strptime(start_time_str, '%Y/%m/%d %H:%M:%S.%f')
                        end_time = datetime.strptime(end_time_str, '%Y/%m/%d %H:%M:%S.%f')
                        delta_time = end_time - start_time  # This returns a timedelta object
                        
                        return {
                            'start_time': start_time_str,
                            'end_time': end_time_str,
                            'delta_time': delta_time,
                            'delta_time_ms': delta_time.total_seconds() * 1000  # Convert to milliseconds
                        }
                    except ValueError as e:
                        messagebox.showerror(f"Error parsing datetime: {e}")
                return None

            def analyze_node(node, parent_timing=None):
                """Recursively analyze a node and its children"""
                node_data = {
                    'node_type': node.tag,
                    'subnodes': []
                }
                
                # Get timing information for this node
                timing_info = get_timing_info(node)
                if timing_info:
                    node_data.update(timing_info)
                elif parent_timing:
                    node_data.update(parent_timing)

                # Get node's direct text if it exists
                if node.text and node.text.strip():
                    node_data['text'] = node.text.strip()

                # Get node's attributes
                if node.attrib:
                    node_data['attributes'] = dict(node.attrib)

                # Process all child nodes
                for child in node:
                    child_data = analyze_node(child, timing_info or parent_timing)
                    if child_data:
                        node_data['subnodes'].append(child_data)

                return node_data

            # Find all query nodes and their timing context
            for node in root.findall('.//*'):
                if '__query' in node.tag:
                    # Find the nearest parent with timing information
                    parent = node
                    parent_timing = None
                    while parent is not None:
                        timing = get_timing_info(parent)
                        if timing:
                            parent_timing = timing
                            break
                        parent = parent.getparent()

                    # Analyze the query node and all its subnodes
                    query_data = analyze_node(node, parent_timing)
                    if query_data:
                        all_query_data.append(query_data)

            # Sort queries by delta time (from highest to lowest)
            all_query_data.sort(key=lambda x: x.get('delta_time_ms', 0), reverse=True)

            # Calculate and add percentage of total time for each query
            if all_query_data:
                total_time_ms = sum((q.get('delta_time_ms', 0) for q in all_query_data))
                if total_time_ms > 0:
                    for query in all_query_data:
                        if 'delta_time_ms' in query:
                            query['percentage_of_total'] = (query['delta_time_ms'] / total_time_ms) * 100

            return all_query_data

        except ET.ParseError as e:
            messagebox.showerror(f"Error parsing XML file: {e}")
            raise


##########################################################

    def only_show_XML_TreeView(self, file_xml):
            try:
                # Create new window
                tree_window = tk.Toplevel()
                tree_window.title("XML Structure Analysis")
                tree_window.geometry("1400x800")

                # Create main frame
                main_frame = ttk.Frame(tree_window)
                main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                # Create tree view with scrollbars
                tree_frame = ttk.Frame(main_frame)
                tree_frame.pack(fill=tk.BOTH, expand=True)

                # Create treeview
                tree = ttk.Treeview(tree_frame)
                
                # Add scrollbars
                vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
                hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
                tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

                # Grid layout
                tree.grid(column=0, row=0, sticky='nsew')
                vsb.grid(column=1, row=0, sticky='ns')
                hsb.grid(column=0, row=1, sticky='ew')
                tree_frame.grid_columnconfigure(0, weight=1)
                tree_frame.grid_rowconfigure(0, weight=1)

                # Configure tree columns
                tree["columns"] = ("tag", "time", "attributes")
                tree.column("#0", width=50, stretch=tk.NO)  # Index column
                tree.column("tag", width=200)
                tree.column("time", width=100)
                tree.column("attributes", width=800)  # Increased width for SQL text

                # Configure tree headings
                tree.heading("#0", text="Index")
                tree.heading("tag", text="Node Type")
                tree.heading("time", text="Execution Time")
                tree.heading("attributes", text="SQL Information")
                
                tree.bind('<Button-3>', lambda event: self.show_sql_popup(tree, event))

                def format_time_delta(delta_time_ms):
                    """Convert milliseconds to a readable format"""
                    if delta_time_ms is None:
                        return "N/A"
                    seconds = delta_time_ms / 1000
                    if seconds < 1:
                        return f"{delta_time_ms:.2f}ms"
                    elif seconds < 60:
                        return f"{seconds:.2f}s"
                    else:
                        minutes = int(seconds // 60)
                        remaining_seconds = seconds % 60
                        return f"{minutes}m {remaining_seconds:.2f}s"

                def get_node_timing(node):
                    """Extract timing information from a node"""
                    start_time_elem = node.find('./__startTime')
                    end_time_elem = node.find('./__endTime')
                    
                    if start_time_elem is not None and end_time_elem is not None:
                        try:
                            start_time_str = start_time_elem.text.strip()
                            end_time_str = end_time_elem.text.strip()
                            
                            start_time = datetime.strptime(start_time_str, '%Y/%m/%d %H:%M:%S.%f') 
                            end_time = datetime.strptime(end_time_str, '%Y/%m/%d %H:%M:%S.%f')
                            delta_time = end_time - start_time
                            
                            return {
                                'delta_time_ms': delta_time.total_seconds() * 1000
                            }
                        except ValueError as e:
                            messagebox.showerror(f"Error parsing datetime: {e}")
                    return None

                def insert_node(parent_id, node, index):
                    """Recursively insert nodes into tree with level-based top 3 highlighting"""
                    # Dictionary to store timing information for each level
                    level_timing = {}
                    
                    def process_level(current_node, current_parent_id, current_index, level=0):
                        """Process nodes at each level, tracking timing information"""
                        # Initialize level in level_timing if not exists
                        if level not in level_timing:
                            level_timing[level] = []

                        # Get timing information
                        timing_info = get_node_timing(current_node)
                        
                        # Prepare node attributes display
                        attr_text = ""
                        if '__query' in current_node.tag:
                            sql_info = []
                            
                            # Check for raw SQL
                            raw_sql = current_node.find('./__rawSQLText')
                            if raw_sql is not None and raw_sql.text:
                                sql_info.append(f"Raw SQL: {raw_sql.text.strip()}")
                            
                            # Check for parsed SQL
                            parsed_sql = current_node.find('./__parsedSQLText')
                            if parsed_sql is not None and parsed_sql.text:
                                sql_info.append(f"Parsed SQL: {parsed_sql.text.strip()}")
                            
                            attr_text = " | ".join(sql_info)
                        
                        # Insert node into tree
                        node_id = tree.insert(current_parent_id, 'end',
                                            values=(current_node.tag,
                                                format_time_delta(timing_info['delta_time_ms'] if timing_info else None),
                                                attr_text),
                                            text=str(current_index))

                        # Store timing information if available
                        if timing_info and timing_info['delta_time_ms']:
                            level_timing[level].append({
                                'node_id': node_id,
                                'node_tag': current_node.tag,
                                'time_ms': timing_info['delta_time_ms']
                            })

                        # Process all child nodes at the next level
                        children = list(current_node)
                        for i, child in enumerate(children):
                            process_level(child, node_id, i + 1, level + 1)

                        # After processing all nodes at this level, highlight top 3
                        if level_timing[level]:
                            # Sort nodes at this level by execution time
                            level_nodes = sorted(level_timing[level], 
                                            key=lambda x: x['time_ms'], 
                                            reverse=True)
                            
                            # Highlight top 3 at this level
                            for i, node_info in enumerate(level_nodes[:3]):
                                tree.item(node_info['node_id'], 
                                        tags=(f'level_{level}_top_{i+1}',))
                                # Configure tag with red color
                                tree.tag_configure(f'level_{level}_top_{i+1}', 
                                                foreground='red')

                    # Start processing from the root level
                    process_level(node, parent_id, index)

                # Create bottom frame for search and analyze button
                bottom_frame = ttk.Frame(main_frame)
                bottom_frame.pack(fill=tk.X, pady=(10, 0))

                # Create search frame on the left side
                search_frame = ttk.Frame(bottom_frame)
                search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)


                # Create analyze button frame on the right side
                analyze_frame = ttk.Frame(bottom_frame)
                analyze_frame.pack(side=tk.RIGHT)

                def analyze_queries():
                    query_data = self.Analyze_XML(file_xml)
                    if query_data:
                        self.show_Result_popup(query_data)

                analyze_button = ttk.Button(
                    analyze_frame, 
                    text="Analyze Queries", 
                    command=analyze_queries,
                    style='Accent.TButton'
                )
                analyze_button.pack(side=tk.RIGHT, padx=(10, 0))

                # Parse XML and populate tree
                try:
                    xml_tree = ET.parse(file_xml)
                    root = xml_tree.getroot()
                    
                    # Create header frame for statistics
                    header_frame = ttk.Frame(main_frame)
                    header_frame.pack(fill=tk.X, pady=(0, 10))

                    # Get the first time encountered (total execution time)
                    def get_first_time(node):
                        timing_info = get_node_timing(node)
                        if timing_info and timing_info['delta_time_ms']:
                            return timing_info['delta_time_ms']
                        for child in node:
                            child_time = get_first_time(child)
                            if child_time is not None:
                                return child_time
                        return None

                    total_time_ms = get_first_time(root)
                    total_time = format_time_delta(total_time_ms) if total_time_ms is not None else "N/A"
                    
                    # Update window title
                    tree_window.title(f"XML Structure Analysis - Total Time: {total_time}")

                    # Create and pack statistics label
                    stats_frame = ttk.Frame(header_frame)
                    stats_frame.pack(side=tk.LEFT, fill=tk.X)
                    
                    stats_label = ttk.Label(stats_frame, 
                                        text=f"Total Execution Time: {total_time}",
                                        font=('Arial', 10, 'bold'))
                    stats_label.pack(anchor='w')

                    # Populate tree
                    insert_node('', root, 1)

                    # Add mousewheel scrolling
                    def on_mousewheel(event):
                        tree.yview_scroll(int(-1*(event.delta/120)), "units")
                    tree.bind('<MouseWheel>', on_mousewheel)
                    '''
                    # Bind keyboard shortcuts
                    tree_window.bind('<Control-f>', lambda e: search_entry.focus())
                    search_entry.bind('<Return>', lambda e: search_tree())
                    '''
                except ET.ParseError as e:
                    messagebox.showerror("Error", f"Error parsing XML file: {e}")
                    tree_window.destroy()
                    return

            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
                if 'tree_window' in locals():
                    tree_window.destroy()






######################################################_________________________________--------------################


    def show_XML_TreeView(self, json_file):
        try:


            xml_filename = json_file.replace('_tree_analysis.json', '.xml')
            
            tree_window = tk.Toplevel()
            tree_window.title("XML Structure Analysis")
            tree_window.geometry("1400x800")

            main_frame = ttk.Frame(tree_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            # Add after creating main_frame and before tree_frame

            #search
            search_frame = ttk.Frame(main_frame)
            search_frame.pack(fill=tk.X, pady=(0, 10))

            search_label = ttk.Label(search_frame, text="Search Content:")
            search_label.pack(side=tk.LEFT, padx=(0, 5))

            search_entry = ttk.Entry(search_frame)
            search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            search_button = ttk.Button(search_frame, text="Search", command=lambda: perform_search())
            search_button.pack(side=tk.LEFT, padx=(5, 0))

            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            tree = ttk.Treeview(tree_frame)
            
            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            tree.grid(column=0, row=0, sticky='nsew')
            vsb.grid(column=1, row=0, sticky='ns')
            hsb.grid(column=0, row=1, sticky='ew')
            tree_frame.grid_columnconfigure(0, weight=1)
            tree_frame.grid_rowconfigure(0, weight=1)

            # Configure tree columns
            tree["columns"] = ("tag", "time", "attribute", "sql")
            tree.column("#0", width=50, stretch=tk.NO)
            tree.column("tag", width=200)
            tree.column("time", width=100)
            tree.column("attribute", width=200)
            tree.column("sql", width=1000, stretch=True)  # Wide column for SQL


            #item=tree.selection()
            #sql_text= tree.item(item)['values']
            tree.bind('<Button-3>', lambda event: self.show_sql_popup(tree, event))
            search_entry.bind("<Return>", lambda event: perform_search())
            tree.bind("<Control-f>", lambda event: search_entry.focus_set())

            tree.heading("#0", text="Index")
            tree.heading("tag", text="Node Type")
            tree.heading("time", text="Execution Time")
            tree.heading("attribute", text="Content")
            tree.heading("sql", text="SQL Query")

            def format_time_delta(delta_time_ms):
                if delta_time_ms is None:
                    return "N/A"
                seconds = delta_time_ms / 1000
                if seconds < 1:
                    return f"{delta_time_ms:.2f}ms"
                elif seconds < 60:
                    return f"{seconds:.2f}s"
                else:
                    minutes = int(seconds // 60)
                    remaining_seconds = seconds % 60
                    return f"{minutes}m {remaining_seconds:.2f}s"

            
            def get_sql_text(node_data):
                """Extract SQL text from node data"""
                if '__query' in node_data['node_type']:
                    # First try to find SQL text in subnodes
                    for subnode in node_data.get('subnodes', []):
                        if subnode['node_type'] == '__parsedSQLText' and 'text' in subnode:
                            return subnode['text']
                        elif subnode['node_type'] == '__rawSQLText' and 'text' in subnode:
                            return subnode['text']
                    
                    # If not found in subnodes, check attributes
                    attributes = node_data.get('attributes', {})
                    if 'rawSQLText' in attributes:
                        return attributes['rawSQLText']
                    elif 'parsedSQLText' in attributes:
                        return attributes['parsedSQLText']
                    
                    # Finally check direct text field
                    if 'text' in node_data:
                        return node_data['text']
                return ""
            
            def get_Content_text(node_data):
                """Extract content text from node data"""
                if  '__startTime' in node_data['node_type'] or '__endTime' in node_data['node_type'] or '__query' in node_data['node_type']:
                    return ""
                    # First try to find SQL text in subnodes
                for subnode in node_data.get('subnodes', []):
                    if '__startTime' not in subnode['node_type'] and '__endTime' not in subnode['node_type'] and '__parsedSQLText' not in subnode['node_type'] and '__rawSQLText' not in subnode['node_type'] and  'text' in subnode:
                        return subnode['text']
                    
                
                # If not found in subnodes, check attributes
                attributes = node_data.get('attributes', {})
                if attributes:
                    return attributes
                
                # Finally check direct text field
                if 'text' in node_data:
                    return node_data['text']
                return ""


            def insert_node(parent_id, node_data, index):
                time_ms = node_data.get('delta_time_ms')
                rank = node_data.get('rank')
                
                # Get SQL text using the get_sql_text function
                sql_text = get_sql_text(node_data)
                content= get_Content_text(node_data)
                
                # Insert node into tree
                node_id = tree.insert(parent_id, 'end',
                                    values=(node_data['node_type'],
                                        format_time_delta(time_ms) if time_ms else "N/A",
                                        content,
                                        sql_text),
                                    text=str(index))

                # Apply red color if node has rank 1, 2, or 3
                if rank in [1, 2, 3]:
                    tree.tag_configure(f'rank_{rank}', foreground='red')
                    tree.item(node_id, tags=(f'rank_{rank}',))

                # Process subnodes
                for i, subnode in enumerate(node_data.get('subnodes', [])):
                    insert_node(node_id, subnode, i + 1)

            def expand_rank1_nodes():
                def traverse_tree(node):
                    # Get all children of the current node
                    children = tree.get_children(node)
                    
                    # Check if current node has rank 1
                    item = tree.item(node)
                    tags = item.get('tags', [])
                    if 'rank_1' in tags:
                        # Expand all parent nodes up to this node
                        parent = tree.parent(node)
                        while parent:
                            tree.item(parent, open=True)
                            parent = tree.parent(parent)
                        # Expand this node
                        tree.item(node, open=True)
                    
                    # Recursively check all children
                    for child in children:
                        traverse_tree(child)
                
                # Start traversal from root nodes
                root_nodes = tree.get_children()
                for root_node in root_nodes:
                    traverse_tree(root_node)


            # Create bottom frame for buttons
            bottom_frame = ttk.Frame(main_frame)
            bottom_frame.pack(fill=tk.X, pady=(10, 0))

            analyze_frame = ttk.Frame(bottom_frame)
            analyze_frame.pack(side=tk.RIGHT)
            expand_frame = ttk.Frame(bottom_frame)
            expand_frame.pack(side=tk.LEFT)


            def analyze_queries():
                query_data = self.Analyze_XML(xml_filename)
                if query_data:
                    self.show_Result_popup(query_data)

            analyze_button = ttk.Button(
                analyze_frame, 
                text="Analyze Queries", 
                command=analyze_queries,
                style='Accent.TButton'
            )
            analyze_button.pack(side=tk.RIGHT, padx=(10, 0))

            expand_rank1_button = ttk.Button(expand_frame, text="Expand Critical nodes", command=lambda: expand_rank1_nodes())
            expand_rank1_button.pack(side=tk.LEFT, padx=(5, 0))

            try:
                with open(json_file, 'r') as f:
                    json_data = json.load(f)

                header_frame = ttk.Frame(main_frame)
                header_frame.pack(fill=tk.X, pady=(0, 10))

                tree_structure = json_data['tree_structure']
                #total_time_ms = tree_structure.get('delta_time_ms')
                #total_time = format_time_delta(total_time_ms) if total_time_ms else "N/A"

                tree_window.title(f"Tree Structure Analysis")

                stats_frame = ttk.Frame(header_frame)
                stats_frame.pack(side=tk.LEFT, fill=tk.X)

                insert_node('', tree_structure, 1)

                def on_mousewheel(event):
                    tree.yview_scroll(int(-1*(event.delta/120)), "units")
                tree.bind('<MouseWheel>', on_mousewheel)

            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Error parsing JSON file: {e}")
                tree_window.destroy()
                return
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while processing JSON: {e}")
                tree_window.destroy()
                return

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            if 'tree_window' in locals():
                tree_window.destroy()




        def expand_all_nodes(tree, item):
            tree.item(item, open=True)
            for child in tree.get_children(item):
                expand_all_nodes(tree, child)

        def collapse_all_nodes(tree, item):
            tree.item(item, open=False)
            for child in tree.get_children(item):
                collapse_all_nodes(tree, child)

        def clear_highlights(tree):
            # Remove highlighting from all items
            for item in tree.tag_has('search_result'):
                tree.item(item, tags=[t for t in tree.item(item)['tags'] if t != 'search_result'])

        def search_tree(tree, item, search_text, found_items):
            # Get the content value (third column)
            values = tree.item(item)['values']
            if values and len(values) > 2:
                content = str(values[2]).lower()
                if search_text.lower() in content:
                    found_items.append(item)
                    # Preserve existing tags and add search_result
                    current_tags = list(tree.item(item)['tags'] or [])
                    if 'search_result' not in current_tags:
                        current_tags.append('search_result')
                    tree.item(item, tags=current_tags)
            
            # Search through all children
            for child in tree.get_children(item):
                search_tree(tree, child, search_text, found_items)

        def perform_search():
            search_text = search_entry.get()
            if not search_text:
                return
            
            # Clear previous highlights
            clear_highlights(tree)
            
            # Configure the search result highlight style
            tree.tag_configure('search_result', background='yellow')
            
            # Collapse all nodes first
            for item in tree.get_children():
                collapse_all_nodes(tree, item)
            
            # Perform search
            found_items = []
            for item in tree.get_children():
                search_tree(tree, item, search_text, found_items)
            
            # Expand paths to found items
            for item in found_items:
                # Expand all parent nodes
                parent = tree.parent(item)
                while parent:
                    tree.item(parent, open=True)
                    parent = tree.parent(parent)
            
            if found_items:
                # Select and focus on the first found item
                tree.selection_set(found_items[0])
                tree.see(found_items[0])
                messagebox.showinfo("Search Results", f"Found {len(found_items)} matches.")
            else:
                messagebox.showinfo("Search Results", "No matches found.")










    def show_sql_popup(self, tree, event):  # Change coordinates to event
        # Get item at coordinates
        item = tree.identify_row(event.y)
        if item:
            # Get values from the item
            values = tree.item(item)['values']
            if values and len(values) > 2:
                if  len(values) > 3:
                    sql_text = values[3]  # Get SQL text from third column
                    content = values[2]
                else:
                    sql_text=values[2]

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
                if sql_text:
                    text_widget.insert(tk.END, sql_text)
                elif content:
                    text_widget.insert(tk.END, content)

                text_widget.config(state='disabled')  # Make it read-only

#-------------------------------------------------------------------------------------------------------------




    async def create_xml_file(self, xml_content_list, filename):
        """Create prettified XML and JSON-analysis files from raw XML content."""
        filename = filename.split('.')[0]
        
        if  os.path.isdir(filename):
            os.chdir(filename)
        else:
            os.makedirs(filename)
            os.chdir(filename)

        if xml_content_list:
            try:
                # Original XML creation logic
                root = ET.fromstring(xml_content_list)
                tree = ET.ElementTree(root)
                
                xml_str = ET.tostring(root, encoding='unicode')
                dom = minidom.parseString(xml_str)
                pretty_xml = dom.toprettyxml(indent="  ")
                pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
                
                with open(f"{filename}.xml", "w", encoding="utf-8") as f:
                    f.write(pretty_xml)

                def extract_timing_info(node):
                    start_time = node.find('./__startTime')
                    end_time = node.find('./__endTime')
                    
                    if start_time is not None and end_time is not None:
                        try:
                            start_time_str = start_time.text.strip()
                            end_time_str = end_time.text.strip()
                            start = datetime.strptime(start_time_str, '%Y/%m/%d %H:%M:%S.%f')
                            end = datetime.strptime(end_time_str, '%Y/%m/%d %H:%M:%S.%f')
                            delta = end - start
                            return {
                                'start_time': start_time_str,
                                'end_time': end_time_str,
                                'delta_time_ms': delta.total_seconds() * 1000
                            }
                        except ValueError as e:
                            messagebox.showerror(f"DateTime parsing error: {e}")
                    return None

                def process_node(node, level=0):
                    node_data = {
                        'node_type': node.tag,
                        'level': level,
                        'rank': None,  # Default rank is None
                        'attributes': dict(node.attrib) if node.attrib else {},
                        'subnodes': []
                    }
                    
                    timing = extract_timing_info(node)
                    if timing:
                        node_data.update(timing)
                    
                    if node.text and node.text.strip():
                        node_data['text'] = node.text.strip()

                    # Process children
                    children_at_level = []
                    for child in node:
                        child_data = process_node(child, level + 1)
                        if child_data:
                            children_at_level.append(child_data)
                            node_data['subnodes'].append(child_data)

                    # Sort and rank children at this level if they have timing information
                    if children_at_level:
                        # Filter children with timing information
                        timed_children = [c for c in children_at_level if 'delta_time_ms' in c]
                        if timed_children:
                            # Sort by duration
                            timed_children.sort(key=lambda x: x['delta_time_ms'], reverse=True)
                            
                            # Calculate total time for this level
                            total_level_time = sum(c['delta_time_ms'] for c in timed_children)
                            
                            if total_level_time > 0:  # Only process if there's actual timing data
                                # Assign ranks to top 3
                                for i, child in enumerate(timed_children[:3]):
                                    child['rank'] = i + 1
                                    child['is_top_three'] = True
                                    child['percentage_of_level'] = (child['delta_time_ms'] / total_level_time * 100)

                    return node_data

                # Process the entire tree
                tree_data = process_node(root)

                # Create final JSON structure
                json_data = {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'source_file': f"{filename}.xml",
                    'tree_structure': tree_data
                }

                # Write JSON file
                json_filename = f"{filename}_tree_analysis.json"
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, default=str)

            except ET.ParseError as e:
                messagebox.showerror(f"XML parsing error: {e}")
            except Exception as e:
                messagebox.showerror(f"Error processing files: {e}")
                
                raise  # Add this to see the full error traceback

    def start_async_processing(self):
        """Start async XML file creation in background"""
        def async_worker():
            async def create_xml_files():
                try:
                    await self.create_xml_file(''.join(self.response),self.file)
                except Exception as e:
                    messagebox.showerror(f"Error in XML file creation: {e}")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(create_xml_files())
            finally:
                loop.close()

        #Start processing in background thread
        self.processing_thread = threading.Thread(target=async_worker, daemon=True)
        self.processing_thread.start()
    
    # ── Log Parsing Engine ──────────────────────────────────────

