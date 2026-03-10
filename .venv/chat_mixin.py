"""
Chat Mixin — SiemensGPT Chat Popup
=====================================

Provides the LLM chat interface popup and text utilities
for interacting with SiemensGPT from within LogTreeView.

Author : Ergito Shkezi
Project: Master's Thesis 2026
"""

import tkinter as tk
from tkinter import messagebox, ttk

from llm_client import SiemensGPT


class ChatMixin:
    """Mixin providing SiemensGPT chat popup functionality."""

    def open_popup(self):
        """Open the SiemensGPT chat popup window."""
        # Create the popup window
        self.popup = tk.Toplevel()
        self.popup.title("SiemensGPT")
        self.popup.geometry("600x500")
        self.popup.configure(bg="#f1f1f1")
         
        # Add content to the popup window
        popup_frame = tk.Frame(self.popup, bg="#f1f1f1")
        popup_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        popup_label = tk.Label(popup_frame, text="SiemensGPT", font=("Arial", 18, "bold"), bg="#f1f1f1", fg="#333333")
        popup_label.pack(pady=10)

        self.selected_rows_label = tk.Label(popup_frame, text="Insert The Log Rows You Want To Analyze:", font=("Arial", 14), bg="#f1f1f1", fg="#333333")
        self.selected_rows_label.pack(pady=5)

        self.selected_rows_text = tk.Text(popup_frame, height=5, width=60, wrap=tk.WORD, font=("Arial", 12), bg="#f8f8f8", fg="#333333", borderwidth=2, relief="groove")
        self.selected_rows_text.pack(pady=10, fill=tk.BOTH, expand=True)

        self.selected_rows_text_scrollbar = ttk.Scrollbar(self.selected_rows_text, orient=tk.VERTICAL, command=self.selected_rows_text.yview)
        self.selected_rows_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.selected_rows_text.configure(yscrollcommand=self.selected_rows_text_scrollbar.set)

            # Add clear button for selected_rows_text
    # Add clear button for selected_rows_text
        self.selected_rows_clear_button = tk.Button(self.selected_rows_text, text="Clear_Log", font=("Arial", 7), bg="#FF6347", fg="black", command=self.clear_text_log)
        self.selected_rows_clear_button.place(relx=0.95, rely=0.02, anchor="ne")

        self.ask_rows_label = tk.Label(popup_frame, text="Make Your Questions:", font=("Arial", 14), bg="#f1f1f1", fg="#333333")
        self.ask_rows_label.pack(pady=5)

        self.ask_rows_text = tk.Text(popup_frame, height=3, width=60, wrap=tk.WORD, font=("Arial", 12), bg="#f8f8f8", fg="#333333", borderwidth=2, relief="groove")
        self.ask_rows_text.pack(pady=10, fill=tk.BOTH, expand=True)

        self.ask_rows_text_scrollbar = ttk.Scrollbar(self.ask_rows_text, orient=tk.VERTICAL, command=self.ask_rows_text.yview)
        self.ask_rows_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ask_rows_text.configure(yscrollcommand=self.ask_rows_text_scrollbar.set)

    # Add clear button for ask_rows_text
        self.ask_rows_clear_button = tk.Button(self.ask_rows_text, text="Clear_Answer", font=("Arial", 7), bg="#FF6347", fg="black", command=self.clear_text)
        self.ask_rows_clear_button.place(relx=0.95, rely=0.02, anchor="ne")


# Add Time Button
        self.toggle_button = tk.Button(popup_frame, text="Use XML Processing", font=("Arial", 11), bg="White", fg="Blue", command=self.Time_Analysis)
        self.toggle_button.pack(side=tk.BOTTOM, pady=10, padx=20)

        # Add the Compare button
        self.compare_button = tk.Button(popup_frame, text="Compare Files", font=("Arial", 11), bg="#FF8C00", fg="Black", command=lambda: self.select_file_to_compare("Tab2"))
        self.compare_button.pack(side=tk.RIGHT, pady=10, padx=10)


        self.print_button = tk.Button(popup_frame, text="Ask SiemensGPT", font=("Arial", 11), bg="#4CAF50", fg="white", command=self.Ask_SiemensGPT)
        self.print_button.pack(side=tk.LEFT, pady=10, padx=10)

        popup_frame.bind_all('<Return>', lambda event: self.Ask_SiemensGPT())


    def clear_text(self):
        self.ask_rows_text.delete("1.0", tk.END)

    def clear_text_log(self):
        self.selected_rows_text.delete("1.0", tk.END)



    def Ask_SiemensGPT(self):

        selected_rows_text = self.selected_rows_text.get("1.0", tk.END).strip()
        ask_rows_text = self.ask_rows_text.get("1.0", tk.END).strip()

        if self.selected_rows_text and ask_rows_text:
            self.ask_rows_text.tag_configure("green", foreground="green")
            self.ask_rows_text.insert(tk.END,("\n"+SiemensGPT(selected_rows_text, ask_rows_text, self.api_key)),"green")
            self.ask_rows_text.insert(tk.END,"\n" )
        else:
            if not selected_rows_text:
                messagebox.showerror("Please Select The Log Rows To Be Analyzed ")
            if not ask_rows_text:
               messagebox.showerror("Please Make A Question")

    # ── XML File Generation ────────────────────────────────────

