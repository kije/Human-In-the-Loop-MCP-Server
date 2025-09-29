#!/usr/bin/env python3
"""
GUI Executor for Human-in-the-Loop MCP Server
This file should be saved as 'gui_executor.py' in the same directory as the main server file.
"""

import sys
import pickle
import tkinter as tk
import platform
import os

CURRENT_PLATFORM = platform.system().lower()
IS_WINDOWS = CURRENT_PLATFORM == 'windows'
IS_MACOS = CURRENT_PLATFORM == 'darwin'
IS_LINUX = CURRENT_PLATFORM == 'linux'

def get_system_font():
    if IS_MACOS:
        return ("SF Pro Display", 13)
    elif IS_WINDOWS:
        return ("Segoe UI", 10)
    else:
        return ("Ubuntu", 10)

def get_title_font():
    if IS_MACOS:
        return ("SF Pro Display", 16, "bold")
    elif IS_WINDOWS:
        return ("Segoe UI", 14, "bold")
    else:
        return ("Ubuntu", 14, "bold")

def get_text_font():
    if IS_MACOS:
        return ("Monaco", 12)
    elif IS_WINDOWS:
        return ("Consolas", 11)
    else:
        return ("Ubuntu Mono", 10)

def get_theme_colors():
    if IS_WINDOWS:
        return {
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F8F9FA",
            "fg_primary": "#202124",
            "fg_secondary": "#5F6368",
            "accent_color": "#0078D4",
            "selection_bg": "#E3F2FD",
        }
    elif IS_MACOS:
        return {
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F5F5F7",
            "fg_primary": "#1D1D1F",
            "fg_secondary": "#86868B",
            "accent_color": "#007AFF",
            "selection_bg": "#E3F2FD",
        }
    else:
        return {
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F8F9FA",
            "fg_primary": "#202124",
            "fg_secondary": "#5F6368",
            "accent_color": "#1976D2",
            "selection_bg": "#E3F2FD",
        }

class SimpleInputDialog:
    def __init__(self, title, prompt, default_value="", input_type="text"):
        self.result = None
        self.input_type = input_type
        
        # Create root window
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("400x200")
        
        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create widgets
        tk.Label(self.root, text=prompt, wraplength=350).pack(pady=20)
        
        self.entry = tk.Entry(self.root, width=40)
        self.entry.pack(pady=10)
        
        if default_value:
            self.entry.insert(0, default_value)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        self.entry.focus_set()
        self.root.bind('<Return>', lambda e: self.ok_clicked())
        self.root.bind('<Escape>', lambda e: self.cancel_clicked())
        
        # Run the main loop
        self.root.mainloop()
    
    def ok_clicked(self):
        value = self.entry.get()
        if self.input_type == "integer":
            try:
                self.result = int(value) if value else None
            except ValueError:
                self.result = None
        elif self.input_type == "float":
            try:
                self.result = float(value) if value else None
            except ValueError:
                self.result = None
        else:
            self.result = value if value else None
        self.root.quit()
        self.root.destroy()
    
    def cancel_clicked(self):
        self.result = None
        self.root.quit()
        self.root.destroy()

class SimpleConfirmationDialog:
    def __init__(self, title, message):
        self.result = False
        
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("400x150")
        
        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        tk.Label(self.root, text=message, wraplength=350).pack(pady=20)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Yes", command=self.yes_clicked).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="No", command=self.no_clicked).pack(side=tk.LEFT, padx=5)
        
        self.root.bind('<Return>', lambda e: self.yes_clicked())
        self.root.bind('<Escape>', lambda e: self.no_clicked())
        
        self.root.mainloop()
    
    def yes_clicked(self):
        self.result = True
        self.root.quit()
        self.root.destroy()
    
    def no_clicked(self):
        self.result = False
        self.root.quit()
        self.root.destroy()

class SimpleInfoDialog:
    def __init__(self, title, message):
        self.result = True
        
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("400x150")
        
        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        tk.Label(self.root, text=message, wraplength=350).pack(pady=20)
        
        tk.Button(self.root, text="OK", command=self.ok_clicked).pack(pady=10)
        
        self.root.bind('<Return>', lambda e: self.ok_clicked())
        self.root.bind('<Escape>', lambda e: self.ok_clicked())
        
        self.root.mainloop()
    
    def ok_clicked(self):
        self.result = True
        self.root.quit()
        self.root.destroy()

class SimpleChoiceDialog:
    def __init__(self, title, prompt, choices, allow_multiple=False):
        self.result = None
        
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("400x300")
        
        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        tk.Label(self.root, text=prompt, wraplength=350).pack(pady=10)
        
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(
            list_frame, 
            selectmode=tk.MULTIPLE if allow_multiple else tk.SINGLE,
            yscrollcommand=scrollbar.set
        )
        self.listbox.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        for choice in choices:
            self.listbox.insert(tk.END, choice)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        if choices:
            self.listbox.selection_set(0)
        
        self.root.bind('<Return>', lambda e: self.ok_clicked())
        self.root.bind('<Escape>', lambda e: self.cancel_clicked())
        
        self.root.mainloop()
    
    def ok_clicked(self):
        selection = self.listbox.curselection()
        if selection:
            selected_items = [self.listbox.get(i) for i in selection]
            self.result = selected_items if len(selected_items) > 1 else selected_items[0]
        self.root.quit()
        self.root.destroy()
    
    def cancel_clicked(self):
        self.result = None
        self.root.quit()
        self.root.destroy()

class SimpleMultilineDialog:
    def __init__(self, title, prompt, default_value=""):
        self.result = None
        
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("500x400")
        
        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        tk.Label(self.root, text=prompt, wraplength=450).pack(pady=10)
        
        text_frame = tk.Frame(self.root)
        text_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text_widget = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set)
        self.text_widget.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.config(command=self.text_widget.yview)
        
        if default_value:
            self.text_widget.insert("1.0", default_value)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        self.root.bind('<Control-Return>', lambda e: self.ok_clicked())
        self.root.bind('<Escape>', lambda e: self.cancel_clicked())
        
        self.text_widget.focus_set()
        self.root.mainloop()
    
    def ok_clicked(self):
        self.result = self.text_widget.get("1.0", tk.END).strip()
        self.root.quit()
        self.root.destroy()
    
    def cancel_clicked(self):
        self.result = None
        self.root.quit()
        self.root.destroy()

def main():
    """Main entry point - this runs on the main thread of the subprocess"""
    # Read parameters from stdin
    params_data = sys.stdin.buffer.read()
    params = pickle.loads(params_data)
    
    dialog_type = params["dialog_type"]
    dialog_params = params["params"]
    
    result = None
    
    try:
        # Activate the application on macOS
        if IS_MACOS:
            try:
                import subprocess
                subprocess.run([
                    'osascript', '-e', 
                    f'tell application "System Events" to set frontmost of first process whose unix id is {os.getpid()} to true'
                ], check=False, capture_output=True, timeout=1)
            except:
                pass
        
        # Create the appropriate dialog
        if dialog_type == "input":
            dialog = SimpleInputDialog(
                dialog_params["title"], 
                dialog_params["prompt"],
                dialog_params.get("default_value", ""),
                dialog_params.get("input_type", "text")
            )
            result = dialog.result
            
        elif dialog_type == "confirmation":
            dialog = SimpleConfirmationDialog(
                dialog_params["title"],
                dialog_params["message"]
            )
            result = dialog.result
            
        elif dialog_type == "info":
            dialog = SimpleInfoDialog(
                dialog_params["title"],
                dialog_params["message"]
            )
            result = dialog.result
            
        elif dialog_type == "choice":
            dialog = SimpleChoiceDialog(
                dialog_params["title"],
                dialog_params["prompt"],
                dialog_params["choices"],
                dialog_params.get("allow_multiple", False)
            )
            result = dialog.result
            
        elif dialog_type == "multiline":
            dialog = SimpleMultilineDialog(
                dialog_params["title"],
                dialog_params["prompt"],
                dialog_params.get("default_value", "")
            )
            result = dialog.result
            
    except Exception as e:
        result = {"error": str(e)}
    
    # Write result to stdout
    sys.stdout.buffer.write(pickle.dumps(result))
    sys.stdout.flush()

if __name__ == "__main__":
    # Ensure this runs on the main thread
    main()
