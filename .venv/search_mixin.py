"""
Search Mixin — Search, Highlight & Navigation
================================================

Provides search, highlight, and result-navigation methods for LogTreeView.

Author : Ergito Shkezi
Project: Master's Thesis 2026
"""

import tkinter as tk
from tkinter import messagebox


class SearchMixin:
    """Mixin providing search and highlight functionality."""

    def delete_search(self):
        self.log_text.tag_remove("search_highlight", "1.0", tk.END)
        self.log_text.tag_remove("highlight", "1.0", tk.END)
        self.Search_Count.config(text="")
        
    # ── Search ─────────────────────────────────────────────────

    def search_log(self):
        """Search log lines for the text in the search entry and highlight results."""
        self.total_search_found=0

        search_term = self.search_entry.get().lower()
        self.log_text.tag_remove("search_highlight", "1.0", tk.END)

        # Get current cursor position
        current_pos = self.log_text.index(tk.INSERT)
        current_line = int(current_pos.split('.')[0])

        self.search_results = []
        
        # First search from current position to end
        for line_number in range(current_line, len(self.log_lines) + 1):
            line = self.log_lines[line_number - 1]
            if search_term in line.lower():
                start_index = f"{line_number}.0"
                end_index = f"{line_number}.{len(line)}"
                self.search_results.append((start_index, end_index))
                self.log_text.tag_add("search_highlight", start_index, end_index)


        # If no results found after current position, search from beginning to current position
        if not self.search_results:
            for line_number in range(1, current_line):
                line = self.log_lines[line_number - 1]
                if search_term in line.lower():
                    start_index = f"{line_number}.0"
                    end_index = f"{line_number}.{len(line)}"
                    self.search_results.append((start_index, end_index))
                    self.log_text.tag_add("search_highlight", start_index, end_index)

        self.log_text.tag_config("search_highlight", background="light green")
        self.total_search_found=len(self.search_results)
        self.Search_Count.config(text=f"{self.total_search_found}")
        
        if self.search_results:
            
            self.current_result_index = 0
            # Get the first match position
            first_match = self.search_results[self.current_result_index][0]
            
            # Calculate the relative position for scrolling
            total_lines = float(self.log_text.index('end-1c').split('.')[0])
            current_line = float(first_match.split('.')[0])
            relative_position = current_line / total_lines if total_lines > 0 else 0
            
            # Scroll both widgets to the same relative position
            self.log_text.yview_moveto(relative_position)
            self.tree.yview_moveto(relative_position)
            
            # Ensure the matched text is visible
            self.log_text.see(first_match)
            
            # Find and select corresponding tree item
            line_number = int(first_match.split('.')[0])
            self.highlight_corresponding_tree_item(line_number)
            
            self.log_text.focus_set()

    def highlight_corresponding_tree_item(self, line_number):
        # Get all items in the tree
        items = self.tree.get_children()
        
        # Find the corresponding item based on line number
        # You'll need to modify this based on how your tree items correspond to log lines
        for item in items:
            # Assuming you store line numbers in the tree items
            # You might need to adjust this logic based on your actual implementation
            item_text = self.tree.item(item)['values'][0]  # Adjust index as needed
            if str(line_number) in str(item_text):
                # Select and see the item
                self.tree.selection_set(item)
                self.tree.see(item)
                break


    def next_search_result(self):
        if self.search_results:
            # Update the index with wrapping
            self.current_result_index = (self.current_result_index + 1) % len(self.search_results)
            self.Search_Count.config(text=f"{self.total_search_found} \\ {self.current_result_index+1}")

            
            # Get the current match position
            start_index, end_index = self.search_results[self.current_result_index]
            
            # Calculate the relative position for scrolling
            total_lines = float(self.log_text.index('end-1c').split('.')[0])
            current_line = float(start_index.split('.')[0])
            relative_position = current_line / total_lines if total_lines > 0 else 0
            
            # Scroll both widgets to the same relative position
            self.log_text.yview_moveto(relative_position)
            self.tree.yview_moveto(relative_position)
            
            # Ensure the matched text is visible
            self.log_text.see(start_index)
            
            # Find and select corresponding tree item
            line_number = int(start_index.split('.')[0])
            self.highlight_corresponding_tree_item(line_number)
            
            self.log_text.focus_set()


    def prev_search_result(self):
        if self.search_results:
            # Update the index with wrapping
            self.current_result_index = (self.current_result_index - 1) % len(self.search_results)
            
            # Get the current match position
            start_index, end_index = self.search_results[self.current_result_index]
            self.Search_Count.config(text=f"{self.total_search_found} \\ {self.current_result_index+1}")
            # Calculate the relative position for scrolling
            total_lines = float(self.log_text.index('end-1c').split('.')[0])
            current_line = float(start_index.split('.')[0])
            relative_position = current_line / total_lines if total_lines > 0 else 0
            
            # Scroll both widgets to the same relative position
            self.log_text.yview_moveto(relative_position)
            self.tree.yview_moveto(relative_position)
            
            # Ensure the matched text is visible
            self.log_text.see(start_index)
            
            # Find and select corresponding tree item
            line_number = int(start_index.split('.')[0])
            self.highlight_corresponding_tree_item(line_number)
            
            self.log_text.focus_set()



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

    def highlight_log_line(self, event):
        try:
            selected_item = self.tree.selection()[0]
            tags = self.tree.item(selected_item, 'tags')

            # Find the tag that starts with "line_" to get the line number
            line_number = None
            for tag in tags:
                if tag.startswith("line_"):
                    line_number = int(tag.split("_")[1])
                    break

            if line_number is None:
                return

            # Clear previous highlights
            self.log_text.tag_remove("highlight", "1.0", tk.END)

            # Check if line number is valid
            if 0 <= line_number < len(self.log_lines):
                # Instead of reinserting all text, just add highlight tag
                start = f"{line_number + 1}.0"
                end = f"{line_number + 1}.end"
                self.log_text.tag_add("highlight", start, end)
                self.log_text.see(start)
            else:
                messagebox.showerror("Error", f"Invalid line number: {line_number}")
        except Exception as e:
            messagebox.showerror("Error", f"Error in highlighting: {e}")


# ══════════════════════════════════════════════════════════════════════
#  SECTION 4 — Configuration & Entry Point
# ══════════════════════════════════════════════════════════════════════

