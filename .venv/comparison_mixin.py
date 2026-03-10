"""
Comparison Mixin — Side-by-Side File Comparison
==================================================

Provides methods for comparing two log files and displaying
the results in a side-by-side popup window.

Author : Ergito Shkezi
Project: Master's Thesis 2026
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QProgressDialog

from comparison import find_matching_sublists, tokenize
from file_utils import read_lines_list
from llm_client import compareGPT


class ComparisonMixin:
    """Mixin providing file comparison functionality."""

    def show_comparison_popup(self, d1, d2, ex_1_in_f2, ex_2_in_f1, i1, i2, file2_name):
        """Display side-by-side comparison results in a popup window."""
        # Create the popup window
        self.popup = tk.Toplevel(self)
        self.popup.title("Comparison Result")
        self.popup.geometry("1200x600")

        # Create a frame to hold the text areas, search components, and the common scrollbar
        main_frame = tk.Frame(self.popup)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create a frame to hold the search components
        search_frame = tk.Frame(main_frame)
        search_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=0)

        
        # Search components for File 1
     # Create a frame to hold the File 1 name label

        self.F1_name = tk.Label(search_frame, text=self.file, font=("impact", 10), bg="#f1f1f1", fg="Black")
        self.F1_name.pack(side=tk.LEFT, fill=tk.Y, anchor="center")

        
        # Search components for File 2
     # Create a frame to hold the File 2 name label

        self.F2_name = tk.Label(search_frame, text=os.path.basename(file2_name), font=("impact", 10), bg="#f1f1f1", fg="Black")
        self.F2_name.pack(side=tk.RIGHT, fill=tk.Y)


        # Create a frame to hold the text areas and the common scrollbar
        frame = tk.Frame(main_frame)
        frame.pack(fill=tk.BOTH, expand=True)

        # Create a common vertical scrollbar
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)

        # Left Text Area (File 1)
        left_text = tk.Text(frame, wrap=tk.WORD, width=60, height=30, yscrollcommand=scrollbar.set)
        left_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right Text Area (File 2)
        right_text = tk.Text(frame, wrap=tk.WORD, width=60, height=30, yscrollcommand=scrollbar.set)
        right_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.right_text=right_text
        self.left_text=left_text

        # Attach the scrollbar to the text areas
        scrollbar.config(command=lambda *args: self.sync_scroll(left_text, right_text, *args))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure tags for highlighting
        left_text.tag_configure("foreground", foreground="Orange")
        right_text.tag_configure("foreground", foreground="Orange") #orange foreground

        left_text.tag_configure("blue_highlight", background="white", foreground="Blue")
        right_text.tag_configure("green_highlight", background="yellow", foreground="black")
        right_text.tag_configure("blue_highlight", background="white", foreground="Blue")
        left_text.tag_configure("orange_highlight", background="white", foreground="Orange")
        right_text.tag_configure("orange_highlight", background="white", foreground="Orange")
    #Visual porpouse
        right_text.insert(tk.END, os.path.basename(file2_name)+ "\n")
        right_text.insert(tk.END, "\n")
        left_text.insert(tk.END, self.file + "\n")
        left_text.insert(tk.END, "\n")

# Populate left text area (File 1)
        for idx, line in enumerate(d1):  # Loop through d1
            apply_orange = idx in i2  # Check if the index is in i2

            while "@@" in line or "##" in line:
                if "@@" in line:
                    pre_text, mark, rest = line.partition("@@")
                    left_text.insert(tk.END, pre_text, "foreground" if apply_orange else None)

                    if "@@" in rest:
                        marked_token, _, remaining = rest.partition("@@")
                        left_text.insert(tk.END, marked_token, "green_highlight")
                        line = remaining
                    else:
                        left_text.insert(tk.END, rest, "foreground" if apply_orange else None)
                        break

                elif "##" in line:
                    pre_text, mark, rest = line.partition("##")
                    left_text.insert(tk.END, pre_text, "foreground" if apply_orange else None)

                    if "##" in rest:
                        marked_token, _, remaining = rest.partition("##")
                        left_text.insert(tk.END, marked_token, "blue_highlight")
                        line = remaining
                    else:
                        left_text.insert(tk.END, rest, "foreground" if apply_orange else None)
                        break
            else:
                left_text.insert(tk.END, line + "\n", "foreground" if apply_orange else None)

            # Add an extra newline for spacing
            left_text.insert(tk.END, "\n")


        # Populate right text area (File 2)
        for idx, line in enumerate(d2):
            
            apply_orange = idx in i1  # Check if index is in i1
            
            while "@@" in line or "##" in line:
                if "@@" in line:
                    pre_text, mark, rest = line.partition("@@")
                    right_text.insert(tk.END, pre_text, "foreground" if apply_orange else None)
                    
                    if "@@" in rest:
                        marked_token, _, remaining = rest.partition("@@")
                        right_text.insert(tk.END, marked_token, "green_highlight")
                        line = remaining
                    else:
                        right_text.insert(tk.END, rest, "foreground" if apply_orange else None)
                        break
                elif "##" in line:
                    pre_text, mark, rest = line.partition("##")
                    right_text.insert(tk.END, pre_text, "foreground" if apply_orange else None)
                    
                    if "##" in rest:
                        marked_token, _, remaining = rest.partition("##")
                        right_text.insert(tk.END, marked_token, "blue_highlight")
                        line = remaining
                    else:
                        right_text.insert(tk.END, rest, "foreground" if apply_orange else None)
                        break
            else:
                right_text.insert(tk.END, line + "\n", "foreground" if apply_orange else None)
            right_text.insert(tk.END, "\n")


            
        if ex_1_in_f2:
            for item in ex_1_in_f2:
                right_text.insert(tk.END, "\n")
                if item.startswith("[FOUND"):
                    right_text.insert(tk.END, item.strip('[FOUND]')+"\n", "orange_highlight")
                elif item.startswith("[NOT FOUND]"):
                    right_text.insert(tk.END, item.strip("[NOT FOUND]") +"\n", "blue_highlight")
                    
        if ex_2_in_f1:
            for item in ex_2_in_f1:
                left_text.insert(tk.END,  "\n")
                if item.startswith("[FOUND"):
                    left_text.insert(tk.END, item.strip('[FOUND]') +"\n", "orange_highlight")
                elif  item.startswith("[NOT FOUND]"):
                    left_text.insert(tk.END, item.strip('[NOT FOUND]')+"\n", "blue_highlight")
                
        #popup=Toplevel()




    def sync_scroll(self, text1, text2, *args):
        """Synchronize scrolling between two text widgets."""
        text1.yview(*args)
        text2.yview(*args)




    def select_file_to_compare(self, Tab):
        self.file_to_compare = filedialog.askopenfilename(title="Select file to compare")
        if self.file_to_compare:
          
            file_2 = read_lines_list(self.file_to_compare)
            d1,d2,extra_1_in_file2,extra_2_in_file1,index_found_1,index_found_2= self.compare_(self.log_lines_compare,file_2,Tab)


            # Show differences in a new popup window
            self.show_comparison_popup(d1, d2, extra_1_in_file2, extra_2_in_file1,index_found_1,index_found_2, self.file_to_compare)
            #self.after(0, self.show_comparison_popup, d1, d2, extra_1_in_file2, extra_2_in_file1)

    def compare_(self, file_1, file2,Tab):
        
        file1=[]
        for i in  file_1:
            file1.append(i)

        diff_file2 = []
        diff_rows = []
        diff_file1= []

        e1 = []  # extra rows in file 1
        e2 = []  # extra rows in file 2
        row = 0  # Initialize row


        # Initialize QApplication if it doesn't exist
        if not QApplication.instance():
            app = QApplication(sys.argv)

        # Create QProgressDialog
        progress = QProgressDialog(
            "Processing log lines...",  # labelText
            "Cancel",                   # cancelButtonText
            0,                         # minimum
            100,                       # maximum
            None,                      # parent
            Qt.WindowType.WindowStaysOnTopHint
        )
        progress.setWindowTitle("Progress")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        progress.setValue(0) 
        progress.setMaximum(max(len(file1), len(file2)))
        QApplication.processEvents()


        while row < max(len(file1), len(file2)):  # Continuously check the updated max_length
            
            # Handle extra rows in file2
            if row >= len(file1):
                for extra_row in file2[row:]:
                    e2.append(extra_row)
                break

            # Handle extra rows in file1
            if row >= len(file2):
                for extra_row in file1[row:]:
                    e1.append(extra_row)
                break

            # Tokenize and compare the current rows
            r2, diff_rows, flag = tokenize(file1[row], file2[row], row, diff_rows)

            if flag:
                file1.insert(row, " - ")

            #diff_file1.append(" ")
            diff_file1.append(file1[row])
            #diff_file2.append(" ")
            diff_file2.append(str(file2[row][:29]) + " " + r2)

            row += 1  # Increment row manually
            progress.setValue(row)
            QApplication.processEvents()  # Keep the GUI responsive
            self.update_idletasks()  


        # Filter out timestamps from both files to compare contents without timestamps

        
        if len(e2) != 0:
            e2_r,index_found_2 = find_matching_sublists(file1, e2, diff_rows)
            if Tab !="Main":
                self.ask_rows_text.tag_configure("green", foreground="green")
                self.ask_rows_text.insert(tk.END,("\n Extra rows in File 2 " + compareGPT(e2_r, self.api_key)),"green")
                self.ask_rows_text.insert(tk.END,"\n" )
            for i in e2:
                diff_file1.append("-")
        else:
            e2_r = []
            index_found_2 = []

        if len(e1) != 0:
            for i in e1:
                diff_file2.append("-")
            e1_r,index_found_1 = find_matching_sublists(file2, e1, diff_rows)
            if Tab !="Main":
                self.ask_rows_text.tag_configure("green", foreground="green")
                self.ask_rows_text.insert(tk.END,("\n Extra rows in File 1 " + compareGPT(e1_r, self.api_key)),"green")
                self.ask_rows_text.insert(tk.END,"\n" )
        else:
            e1_r = []
            index_found_1=[]

        
        #file1.insert(0, f"File_1: {self.file} \n")
        return diff_file1, diff_file2, e2_r, e1_r, index_found_1,index_found_2
    



    # ── LLM Integration (SiemensGPT) ─────────────────────────────

