"""
Log Parser Ultimate — Interactive Transaction Log Analyzer
===========================================================

Entry point for the Log Parser Ultimate application.

Run this script to launch the GUI:
    python Log_Parser_Ultimate.py

Author : Ergito Shkëzi
Project: Master's Thesis 2026
"""

# ──────────────────────────────────────────────────────────────────────
# Standard Library
# ──────────────────────────────────────────────────────────────────────
import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

# ──────────────────────────────────────────────────────────────────────
# Local Modules
# ──────────────────────────────────────────────────────────────────────
from log_tree_view import LogTreeView


# ══════════════════════════════════════════════════════════════════════
#  Configuration
# ══════════════════════════════════════════════════════════════════════

CONFIG_FILE = "config.json"
DEFAULT_API_KEY = "SIAK-qFpdpe9lWgR6DKm60mbDjchce97f70a13"


def load_config():
    """Load stored config if it exists, otherwise return an empty dict."""
    if os.path.exists(CONFIG_FILE) and os.path.getsize(CONFIG_FILE) > 0:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config):
    """Save config to file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


# ══════════════════════════════════════════════════════════════════════
#  Main Entry Point
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    config = load_config()
    stored_api_key = config.get("default_api_key", None)

    root = tk.Tk()
    root.withdraw()  # Hide main window initially

    if not stored_api_key:
        user_api_key = simpledialog.askstring("API Key", "Enter API Key (leave blank for default):", parent=root)
        api_key = user_api_key if user_api_key else DEFAULT_API_KEY

        if user_api_key:
            save_as_default = tk.BooleanVar(value=False)
            check_window = tk.Toplevel(root)
            check_window.title("Save API Key")
            check_window.geometry("300x150")
            

            label = tk.Label(check_window, text="Save this API Key as default?")
            label.pack(pady=10)

            check_button = tk.Checkbutton(check_window, text="Save as default", variable=save_as_default)
            check_button.pack()

            def confirm():
                check_window.destroy()
                if save_as_default.get():
                    config["default_api_key"] = api_key
                    save_config(config)

            confirm_button = tk.Button(check_window, text="Confirm", command=confirm)
            confirm_button.pack(pady=10)

            check_window.wait_window()
    else:
        api_key = stored_api_key

   
    while True:
        file_path = filedialog.askopenfilename(
            title="Select Log File",
            filetypes=[
                ("Log files", "*.log"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            messagebox.showerror("No file selected. Exiting...")
            break

        path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        

        log_tree_view = LogTreeView(file_path, file_name, api_key)
        log_tree_view.mainloop() 
        
        # Ask if user wants to open another file

        sys.exit()