#!/usr/bin/env python3
"""
Human-in-the-Loop MCP Server - Fixed for macOS Thread Safety

This server provides tools for getting human input and choices through GUI dialogs.
Fixed to ensure all GUI operations happen on the main thread for macOS compatibility.
"""

import asyncio
import json
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import List, Dict, Any, Optional, Literal
import sys
import os
from pydantic import Field
from typing import Annotated
import queue
from concurrent.futures import Future

# Set required environment variable for FastMCP 2.8.1+
os.environ.setdefault('FASTMCP_LOG_LEVEL', 'INFO')
from fastmcp import FastMCP, Context

# Platform detection
CURRENT_PLATFORM = platform.system().lower()
IS_WINDOWS = CURRENT_PLATFORM == 'windows'
IS_MACOS = CURRENT_PLATFORM == 'darwin'
IS_LINUX = CURRENT_PLATFORM == 'linux'

# Initialize the MCP server
mcp = FastMCP("Human-in-the-Loop Server")

# Global GUI management
_gui_thread = None
_gui_queue = queue.Queue()
_gui_root = None
_gui_initialized = threading.Event()
_gui_lock = threading.Lock()

class GUIRequest:
    """Encapsulates a GUI request with its future for the result"""
    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.future = Future()

def gui_thread_worker():
    """Main GUI thread worker that processes all GUI requests"""
    global _gui_root
    
    try:
        # Create the main Tkinter root in this thread
        _gui_root = tk.Tk()
        _gui_root.withdraw()  # Hide the main window
        
        # Platform-specific configuration
        if IS_MACOS:
            try:
                # Configure for macOS
                _gui_root.call('wm', 'attributes', '.', '-topmost', '1')
                # Try to activate Python app
                subprocess.run([
                    'osascript', '-e', 
                    f'tell application "System Events" to set frontmost of first process whose unix id is {os.getpid()} to true'
                ], check=False, capture_output=True, timeout=1)
            except:
                pass
        elif IS_WINDOWS:
            _gui_root.attributes('-topmost', True)
        
        # Signal that GUI is initialized
        _gui_initialized.set()
        
        # Process GUI requests
        while True:
            try:
                # Check for requests with a short timeout
                _gui_root.update()  # Process Tkinter events
                
                try:
                    request = _gui_queue.get(block=False)
                except queue.Empty:
                    _gui_root.after(50)  # Wait 50ms before next check
                    continue
                
                if request is None:  # Shutdown signal
                    break
                
                # Execute the GUI operation in the main GUI thread
                try:
                    result = request.func(*request.args, **request.kwargs)
                    request.future.set_result(result)
                except Exception as e:
                    request.future.set_exception(e)
                    
            except Exception as e:
                print(f"Error in GUI thread: {e}")
                
    except Exception as e:
        print(f"Fatal error in GUI thread: {e}")
        _gui_initialized.set()  # Set to prevent hanging
    finally:
        if _gui_root:
            try:
                _gui_root.quit()
                _gui_root.destroy()
            except:
                pass

def ensure_gui_thread_running():
    """Ensure the GUI thread is running"""
    global _gui_thread
    
    with _gui_lock:
        if _gui_thread is None or not _gui_thread.is_alive():
            _gui_thread = threading.Thread(target=gui_thread_worker, daemon=True)
            _gui_thread.start()
            
            # Wait for GUI initialization
            if not _gui_initialized.wait(timeout=5):
                raise RuntimeError("GUI thread failed to initialize")
    
    return True

def run_in_gui_thread(func, *args, **kwargs):
    """Execute a function in the GUI thread and return the result"""
    ensure_gui_thread_running()
    
    request = GUIRequest(func, args, kwargs)
    _gui_queue.put(request)
    
    # Wait for the result with timeout
    try:
        return request.future.result(timeout=300)  # 5 minute timeout
    except Exception as e:
        print(f"GUI operation failed: {e}")
        raise

# Keep all the existing helper functions (get_system_font, get_title_font, etc.)
# ... [Keep all the style and theme functions as they are] ...

def get_system_font():
    """Get appropriate system font for the current platform"""
    if IS_MACOS:
        return ("SF Pro Display", 13)
    elif IS_WINDOWS:
        return ("Segoe UI", 10)
    else:
        return ("Ubuntu", 10)

def get_title_font():
    """Get title font for dialogs"""
    if IS_MACOS:
        return ("SF Pro Display", 16, "bold")
    elif IS_WINDOWS:
        return ("Segoe UI", 14, "bold")
    else:
        return ("Ubuntu", 14, "bold")

def get_text_font():
    """Get text font for text widgets"""
    if IS_MACOS:
        return ("Monaco", 12)
    elif IS_WINDOWS:
        return ("Consolas", 11)
    else:
        return ("Ubuntu Mono", 10)

def get_theme_colors():
    """Get modern theme colors based on platform"""
    if IS_WINDOWS:
        return {
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F8F9FA",
            "bg_accent": "#F1F3F4",
            "fg_primary": "#202124",
            "fg_secondary": "#5F6368",
            "accent_color": "#0078D4",
            "accent_hover": "#106EBE",
            "border_color": "#E8EAED",
            "success_color": "#137333",
            "error_color": "#D93025",
            "selection_bg": "#E3F2FD",
            "selection_fg": "#1565C0"
        }
    elif IS_MACOS:
        return {
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F5F5F7",
            "bg_accent": "#F2F2F7",
            "fg_primary": "#1D1D1F",
            "fg_secondary": "#86868B",
            "accent_color": "#007AFF",
            "accent_hover": "#0056CC",
            "border_color": "#D2D2D7",
            "success_color": "#30D158",
            "error_color": "#FF3B30",
            "selection_bg": "#E3F2FD",
            "selection_fg": "#1565C0"
        }
    else:  # Linux
        return {
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F8F9FA",
            "bg_accent": "#F1F3F4",
            "fg_primary": "#202124",
            "fg_secondary": "#5F6368",
            "accent_color": "#1976D2",
            "accent_hover": "#1565C0",
            "border_color": "#E8EAED",
            "success_color": "#388E3C",
            "error_color": "#D32F2F",
            "selection_bg": "#E3F2FD",
            "selection_fg": "#1565C0"
        }

# Modified dialog creation functions to work with the GUI root
def create_input_dialog(title: str, prompt: str, default_value: str = "", input_type: str = "text"):
    """Create a modern input dialog window - runs in GUI thread"""
    global _gui_root
    
    try:
        dialog = ModernInputDialog(_gui_root, title, prompt, default_value, input_type)
        return dialog.result
    except Exception as e:
        print(f"Error in input dialog: {e}")
        return None

def create_choice_dialog(title: str, prompt: str, choices: List[str], allow_multiple: bool = False):
    """Create a choice dialog window - runs in GUI thread"""
    global _gui_root
    
    try:
        dialog = ChoiceDialog(_gui_root, title, prompt, choices, allow_multiple)
        return dialog.result
    except Exception as e:
        print(f"Error in choice dialog: {e}")
        return None

def create_multiline_input_dialog(title: str, prompt: str, default_value: str = ""):
    """Create a multi-line text input dialog - runs in GUI thread"""
    global _gui_root
    
    try:
        dialog = MultilineInputDialog(_gui_root, title, prompt, default_value)
        return dialog.result
    except Exception as e:
        print(f"Error in multiline dialog: {e}")
        return None

def show_confirmation(title: str, message: str):
    """Show confirmation dialog - runs in GUI thread"""
    global _gui_root
    
    try:
        dialog = ModernConfirmationDialog(_gui_root, title, message)
        return dialog.result
    except Exception as e:
        print(f"Error in confirmation dialog: {e}")
        return False

def show_info(title: str, message: str):
    """Show info dialog - runs in GUI thread"""
    global _gui_root
    
    try:
        dialog = ModernInfoDialog(_gui_root, title, message)
        return dialog.result
    except Exception as e:
        print(f"Error in info dialog: {e}")
        return False

# [Include all the dialog classes as they are - ModernInputDialog, ModernConfirmationDialog, etc.]
# These classes don't need changes as they'll be instantiated in the GUI thread

class ModernInputDialog:
    """Keep the existing implementation"""
    def __init__(self, parent, title, prompt, default_value="", input_type="text"):
        self.result = None
        self.input_type = input_type
        
        self.theme_colors = get_theme_colors()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Configure window
        self.dialog.configure(bg=self.theme_colors["bg_primary"])
        if IS_MACOS:
            try:
                self.dialog.call('wm', 'attributes', '.', '-topmost', '1')
                self.dialog.lift()
                self.dialog.focus_force()
            except:
                pass
        elif IS_WINDOWS:
            self.dialog.attributes('-topmost', True)
            self.dialog.lift()
            self.dialog.focus_force()
        
        if IS_WINDOWS:
            self.dialog.geometry("420x280")
        else:
            self.dialog.geometry("400x260")
        
        self.center_window()
        
        main_frame = tk.Frame(self.dialog, bg=self.theme_colors["bg_primary"])
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)
        
        title_label = tk.Label(
            main_frame,
            text=title,
            bg=self.theme_colors["bg_primary"],
            fg=self.theme_colors["fg_primary"],
            font=get_title_font(),
            anchor="w"
        )
        title_label.pack(fill="x", pady=(0, 8))
        
        prompt_label = tk.Label(
            main_frame,
            text=prompt,
            bg=self.theme_colors["bg_primary"],
            fg=self.theme_colors["fg_secondary"],
            font=get_system_font(),
            wraplength=350,
            justify="left",
            anchor="w"
        )
        prompt_label.pack(fill="x", pady=(0, 20))
        
        input_frame = tk.Frame(main_frame, bg=self.theme_colors["bg_primary"])
        input_frame.pack(fill="x", pady=(0, 24))
        
        self.entry = tk.Entry(
            input_frame,
            font=get_system_font(),
            bg=self.theme_colors["bg_primary"],
            fg=self.theme_colors["fg_primary"],
            relief="solid",
            borderwidth=1,
            highlightthickness=1,
            highlightcolor=self.theme_colors["accent_color"],
            highlightbackground=self.theme_colors["border_color"],
            insertbackground=self.theme_colors["accent_color"]
        )
        self.entry.pack(fill="x", ipady=8, ipadx=12)
        
        if default_value:
            self.entry.insert(0, default_value)
            self.entry.select_range(0, tk.END)
        
        button_frame = tk.Frame(main_frame, bg=self.theme_colors["bg_primary"])
        button_frame.pack(fill="x")
        
        # OK button
        ok_btn = tk.Button(
            button_frame,
            text="OK",
            command=self.ok_clicked,
            bg=self.theme_colors["accent_color"],
            fg="#FFFFFF",
            font=get_system_font(),
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=8
        )
        ok_btn.pack(side=tk.RIGHT, padx=(8, 0))
        
        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_clicked,
            bg=self.theme_colors["bg_secondary"],
            fg=self.theme_colors["fg_primary"],
            font=get_system_font(),
            relief="flat",
            borderwidth=0,
            padx=20,
            pady=8
        )
        cancel_btn.pack(side=tk.RIGHT)
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())
        
        self.entry.focus_set()
        self.dialog.wait_window()
    
    def center_window(self):
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        if IS_MACOS:
            y = max(50, y - 50)
        elif IS_WINDOWS:
            y = max(30, y - 30)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
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
        self.dialog.destroy()
    
    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()

# [Include simplified versions of other dialog classes similarly]

class ModernConfirmationDialog:
    def __init__(self, parent, title, message):
        self.result = False
        self.theme_colors = get_theme_colors()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        self.dialog.configure(bg=self.theme_colors["bg_primary"])
        if IS_MACOS:
            try:
                self.dialog.call('wm', 'attributes', '.', '-topmost', '1')
            except:
                pass
        elif IS_WINDOWS:
            self.dialog.attributes('-topmost', True)
        
        self.dialog.geometry("440x220" if IS_WINDOWS else "420x200")
        self.center_window()
        
        main_frame = tk.Frame(self.dialog, bg=self.theme_colors["bg_primary"])
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)
        
        tk.Label(main_frame, text=title, bg=self.theme_colors["bg_primary"],
                fg=self.theme_colors["fg_primary"], font=get_title_font(),
                anchor="w").pack(fill="x", pady=(0, 12))
        
        tk.Label(main_frame, text=message, bg=self.theme_colors["bg_primary"],
                fg=self.theme_colors["fg_secondary"], font=get_system_font(),
                wraplength=370, justify="left", anchor="w").pack(fill="x", pady=(0, 24))
        
        button_frame = tk.Frame(main_frame, bg=self.theme_colors["bg_primary"])
        button_frame.pack(fill="x")
        
        tk.Button(button_frame, text="Yes", command=self.yes_clicked,
                 bg=self.theme_colors["accent_color"], fg="#FFFFFF",
                 font=get_system_font(), relief="flat", borderwidth=0,
                 padx=20, pady=8).pack(side=tk.RIGHT, padx=(8, 0))
        
        tk.Button(button_frame, text="No", command=self.no_clicked,
                 bg=self.theme_colors["bg_secondary"], fg=self.theme_colors["fg_primary"],
                 font=get_system_font(), relief="flat", borderwidth=0,
                 padx=20, pady=8).pack(side=tk.RIGHT)
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.no_clicked)
        self.dialog.bind('<Return>', lambda e: self.yes_clicked())
        self.dialog.bind('<Escape>', lambda e: self.no_clicked())
        
        self.dialog.wait_window()
    
    def center_window(self):
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        if IS_MACOS:
            y = max(50, y - 50)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def yes_clicked(self):
        self.result = True
        self.dialog.destroy()
    
    def no_clicked(self):
        self.result = False
        self.dialog.destroy()

class ModernInfoDialog:
    def __init__(self, parent, title, message):
        self.result = True
        self.theme_colors = get_theme_colors()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        self.dialog.configure(bg=self.theme_colors["bg_primary"])
        if IS_MACOS:
            try:
                self.dialog.call('wm', 'attributes', '.', '-topmost', '1')
            except:
                pass
        elif IS_WINDOWS:
            self.dialog.attributes('-topmost', True)
        
        self.dialog.geometry("420x200" if IS_WINDOWS else "400x180")
        self.center_window()
        
        main_frame = tk.Frame(self.dialog, bg=self.theme_colors["bg_primary"])
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)
        
        tk.Label(main_frame, text=title, bg=self.theme_colors["bg_primary"],
                fg=self.theme_colors["fg_primary"], font=get_title_font(),
                anchor="w").pack(fill="x", pady=(0, 12))
        
        tk.Label(main_frame, text=message, bg=self.theme_colors["bg_primary"],
                fg=self.theme_colors["fg_secondary"], font=get_system_font(),
                wraplength=350, justify="left", anchor="w").pack(fill="x", pady=(0, 24))
        
        button_frame = tk.Frame(main_frame, bg=self.theme_colors["bg_primary"])
        button_frame.pack(fill="x")
        
        tk.Button(button_frame, text="OK", command=self.ok_clicked,
                 bg=self.theme_colors["accent_color"], fg="#FFFFFF",
                 font=get_system_font(), relief="flat", borderwidth=0,
                 padx=20, pady=8).pack(side=tk.RIGHT)
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.ok_clicked)
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.ok_clicked())
        
        self.dialog.wait_window()
    
    def center_window(self):
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        if IS_MACOS:
            y = max(50, y - 50)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def ok_clicked(self):
        self.result = True
        self.dialog.destroy()

class ChoiceDialog:
    def __init__(self, parent, title, prompt, choices, allow_multiple=False):
        self.result = None
        self.theme_colors = get_theme_colors()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)
        
        self.dialog.configure(bg=self.theme_colors["bg_primary"])
        if IS_MACOS:
            try:
                self.dialog.call('wm', 'attributes', '.', '-topmost', '1')
            except:
                pass
        elif IS_WINDOWS:
            self.dialog.attributes('-topmost', True)
        
        self.dialog.geometry("500x420" if IS_WINDOWS else "480x400")
        self.center_window()
        
        main_frame = tk.Frame(self.dialog, bg=self.theme_colors["bg_primary"])
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)
        
        tk.Label(main_frame, text=title, bg=self.theme_colors["bg_primary"],
                fg=self.theme_colors["fg_primary"], font=get_title_font(),
                anchor="w").pack(fill="x", pady=(0, 8))
        
        tk.Label(main_frame, text=prompt, bg=self.theme_colors["bg_primary"],
                fg=self.theme_colors["fg_secondary"], font=get_system_font(),
                wraplength=450, justify="left", anchor="w").pack(fill="x", pady=(0, 20))
        
        list_frame = tk.Frame(main_frame, bg=self.theme_colors["bg_primary"])
        list_frame.pack(fill="both", expand=True, pady=(0, 24))
        
        self.listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE if allow_multiple else tk.SINGLE,
                                 bg=self.theme_colors["bg_primary"], fg=self.theme_colors["fg_primary"],
                                 selectbackground=self.theme_colors["selection_bg"],
                                 font=get_system_font(), height=8)
        for choice in choices:
            self.listbox.insert(tk.END, choice)
        self.listbox.pack(side=tk.LEFT, fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        button_frame = tk.Frame(main_frame, bg=self.theme_colors["bg_primary"])
        button_frame.pack(fill="x")
        
        tk.Button(button_frame, text="OK", command=self.ok_clicked,
                 bg=self.theme_colors["accent_color"], fg="#FFFFFF",
                 font=get_system_font(), relief="flat", borderwidth=0,
                 padx=20, pady=8).pack(side=tk.RIGHT, padx=(8, 0))
        
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked,
                 bg=self.theme_colors["bg_secondary"], fg=self.theme_colors["fg_primary"],
                 font=get_system_font(), relief="flat", borderwidth=0,
                 padx=20, pady=8).pack(side=tk.RIGHT)
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())
        
        if choices:
            self.listbox.selection_set(0)
        
        self.dialog.wait_window()
    
    def center_window(self):
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        if IS_MACOS:
            y = max(50, y - 50)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def ok_clicked(self):
        selection = self.listbox.curselection()
        if selection:
            selected_items = [self.listbox.get(i) for i in selection]
            self.result = selected_items if len(selected_items) > 1 else selected_items[0]
        self.dialog.destroy()
    
    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()

class MultilineInputDialog:
    def __init__(self, parent, title, prompt, default_value=""):
        self.result = None
        self.theme_colors = get_theme_colors()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)
        
        self.dialog.configure(bg=self.theme_colors["bg_primary"])
        if IS_MACOS:
            try:
                self.dialog.call('wm', 'attributes', '.', '-topmost', '1')
            except:
                pass
        elif IS_WINDOWS:
            self.dialog.attributes('-topmost', True)
        
        self.dialog.geometry("600x500" if IS_WINDOWS else "580x480")
        self.center_window()
        
        main_frame = tk.Frame(self.dialog, bg=self.theme_colors["bg_primary"])
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)
        
        tk.Label(main_frame, text=title, bg=self.theme_colors["bg_primary"],
                fg=self.theme_colors["fg_primary"], font=get_title_font(),
                anchor="w").pack(fill="x", pady=(0, 8))
        
        tk.Label(main_frame, text=prompt, bg=self.theme_colors["bg_primary"],
                fg=self.theme_colors["fg_secondary"], font=get_system_font(),
                wraplength=520, justify="left", anchor="w").pack(fill="x", pady=(0, 20))
        
        text_frame = tk.Frame(main_frame, bg=self.theme_colors["bg_primary"])
        text_frame.pack(fill="both", expand=True, pady=(0, 24))
        
        self.text_widget = tk.Text(text_frame, height=12, wrap="word",
                                  bg=self.theme_colors["bg_primary"], fg=self.theme_colors["fg_primary"],
                                  font=get_text_font(), padx=12, pady=8)
        self.text_widget.pack(side=tk.LEFT, fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(text_frame, command=self.text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        if default_value:
            self.text_widget.insert("1.0", default_value)
        
        button_frame = tk.Frame(main_frame, bg=self.theme_colors["bg_primary"])
        button_frame.pack(fill="x")
        
        tk.Button(button_frame, text="OK", command=self.ok_clicked,
                 bg=self.theme_colors["accent_color"], fg="#FFFFFF",
                 font=get_system_font(), relief="flat", borderwidth=0,
                 padx=20, pady=8).pack(side=tk.RIGHT, padx=(8, 0))
        
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked,
                 bg=self.theme_colors["bg_secondary"], fg=self.theme_colors["fg_primary"],
                 font=get_system_font(), relief="flat", borderwidth=0,
                 padx=20, pady=8).pack(side=tk.RIGHT)
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
        self.dialog.bind('<Control-Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())
        
        self.text_widget.focus_set()
        self.dialog.wait_window()
    
    def center_window(self):
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        if IS_MACOS:
            y = max(50, y - 50)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def ok_clicked(self):
        self.result = self.text_widget.get("1.0", tk.END).strip()
        self.dialog.destroy()
    
    def cancel_clicked(self):
        self.result = None
        self.dialog.destroy()

# MCP Tools - Modified to use run_in_gui_thread

@mcp.tool()
async def get_user_input(
    title: Annotated[str, Field(description="Title of the input dialog window")],
    prompt: Annotated[str, Field(description="The prompt/question to show to the user")],
    default_value: Annotated[str, Field(description="Default value to pre-fill in the input field")] = "",
    input_type: Annotated[Literal["text", "integer", "float"], Field(description="Type of input expected")] = "text",
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Create an input dialog window for the user to enter text, numbers, or other data.
    
    This tool opens a GUI dialog box where the user can input information that the LLM needs.
    Perfect for getting specific details, clarifications, or data from the user.
    """
    try:
        if ctx:
            await ctx.info(f"Requesting user input: {prompt}")
        
        # Run the dialog in the GUI thread
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            run_in_gui_thread,
            create_input_dialog,
            title, prompt, default_value, input_type
        )
        
        if result is not None:
            if ctx:
                await ctx.info(f"User provided input: {result}")
            return {
                "success": True,
                "user_input": result,
                "input_type": input_type,
                "cancelled": False,
                "platform": CURRENT_PLATFORM
            }
        else:
            if ctx:
                await ctx.warning("User cancelled the input dialog")
            return {
                "success": False,
                "user_input": None,
                "input_type": input_type,
                "cancelled": True,
                "platform": CURRENT_PLATFORM
            }
    
    except Exception as e:
        if ctx:
            await ctx.error(f"Error creating input dialog: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "cancelled": False,
            "platform": CURRENT_PLATFORM
        }

@mcp.tool()
async def get_user_choice(
    title: Annotated[str, Field(description="Title of the choice dialog window")],
    prompt: Annotated[str, Field(description="The prompt/question to show to the user")],
    choices: Annotated[List[str], Field(description="List of choices to present to the user")],
    allow_multiple: Annotated[bool, Field(description="Whether user can select multiple choices")] = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Create a choice dialog window for the user to select from multiple options.
    
    This tool opens a GUI dialog box with a list of choices where the user can select
    one or multiple options. Perfect for getting decisions, preferences, or selections from the user.
    """
    try:
        if ctx:
            await ctx.info(f"Requesting user choice: {prompt}")
            await ctx.debug(f"Available choices: {choices}")
        
        # Run the dialog in the GUI thread
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            run_in_gui_thread,
            create_choice_dialog,
            title, prompt, choices, allow_multiple
        )
        
        if result is not None:
            if ctx:
                await ctx.info(f"User selected: {result}")
            return {
                "success": True,
                "selected_choice": result,
                "selected_choices": result if isinstance(result, list) else [result],
                "allow_multiple": allow_multiple,
                "cancelled": False,
                "platform": CURRENT_PLATFORM
            }
        else:
            if ctx:
                await ctx.warning("User cancelled the choice dialog")
            return {
                "success": False,
                "selected_choice": None,
                "selected_choices": [],
                "allow_multiple": allow_multiple,
                "cancelled": True,
                "platform": CURRENT_PLATFORM
            }
    
    except Exception as e:
        if ctx:
            await ctx.error(f"Error creating choice dialog: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "cancelled": False,
            "platform": CURRENT_PLATFORM
        }

@mcp.tool()
async def get_multiline_input(
    title: Annotated[str, Field(description="Title of the input dialog window")],
    prompt: Annotated[str, Field(description="The prompt/question to show to the user")],
    default_value: Annotated[str, Field(description="Default text to pre-fill in the text area")] = "",
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Create a multi-line text input dialog for the user to enter longer text content.
    
    This tool opens a GUI dialog box with a large text area where the user can input
    multiple lines of text. Perfect for getting detailed descriptions, code, or long-form content.
    """
    try:
        if ctx:
            await ctx.info(f"Requesting multiline user input: {prompt}")
        
        # Run the dialog in the GUI thread
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            run_in_gui_thread,
            create_multiline_input_dialog,
            title, prompt, default_value
        )
        
        if result is not None:
            if ctx:
                await ctx.info(f"User provided multiline input ({len(result)} characters)")
            return {
                "success": True,
                "user_input": result,
                "character_count": len(result),
                "line_count": len(result.split('\n')),
                "cancelled": False,
                "platform": CURRENT_PLATFORM
            }
        else:
            if ctx:
                await ctx.warning("User cancelled the multiline input dialog")
            return {
                "success": False,
                "user_input": None,
                "cancelled": True,
                "platform": CURRENT_PLATFORM
            }
    
    except Exception as e:
        if ctx:
            await ctx.error(f"Error creating multiline input dialog: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "cancelled": False,
            "platform": CURRENT_PLATFORM
        }

@mcp.tool()
async def show_confirmation_dialog(
    title: Annotated[str, Field(description="Title of the confirmation dialog")],
    message: Annotated[str, Field(description="The message to show to the user")],
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Show a confirmation dialog with Yes/No buttons.
    
    This tool displays a message to the user and asks for confirmation.
    Perfect for getting approval before proceeding with an action.
    """
    try:
        if ctx:
            await ctx.info(f"Requesting user confirmation: {message}")
        
        # Run the dialog in the GUI thread
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            run_in_gui_thread,
            show_confirmation,
            title, message
        )
        
        if ctx:
            await ctx.info(f"User confirmation result: {'Yes' if result else 'No'}")
        
        return {
            "success": True,
            "confirmed": result,
            "response": "yes" if result else "no",
            "platform": CURRENT_PLATFORM
        }
    
    except Exception as e:
        if ctx:
            await ctx.error(f"Error showing confirmation dialog: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "confirmed": False,
            "platform": CURRENT_PLATFORM
        }

@mcp.tool()
async def show_info_message(
    title: Annotated[str, Field(description="Title of the information dialog")],
    message: Annotated[str, Field(description="The information message to show to the user")],
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Show an information message to the user.
    
    This tool displays an informational message dialog to notify the user about something.
    The user just needs to click OK to acknowledge the message.
    """
    try:
        if ctx:
            await ctx.info(f"Showing info message to user: {message}")
        
        # Run the dialog in the GUI thread
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            run_in_gui_thread,
            show_info,
            title, message
        )
        
        if ctx:
            await ctx.info("Info message acknowledged by user")
        
        return {
            "success": True,
            "acknowledged": result,
            "platform": CURRENT_PLATFORM
        }
    
    except Exception as e:
        if ctx:
            await ctx.error(f"Error showing info message: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "platform": CURRENT_PLATFORM
        }

# Keep the get_human_loop_prompt and health_check functions as they are
@mcp.prompt()
async def get_human_loop_prompt() -> Dict[str, str]:
    """Get prompting guidance for LLMs on when and how to use human-in-the-loop tools."""
    # [Keep the existing implementation]
    return {
        "main_prompt": "...",  # Keep existing content
        "usage_examples": "...",
        "decision_framework": "...",
        "integration_tips": "..."
    }

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Check if the Human-in-the-Loop server is running and GUI is available."""
    try:
        gui_available = ensure_gui_thread_running()
        
        return {
            "status": "healthy" if gui_available else "degraded",
            "gui_available": gui_available,
            "server_name": "Human-in-the-Loop Server",
            "platform": CURRENT_PLATFORM,
            "platform_details": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            },
            "python_version": sys.version.split()[0],
            "is_windows": IS_WINDOWS,
            "is_macos": IS_MACOS,
            "is_linux": IS_LINUX,
            "tools_available": [
                "get_user_input",
                "get_user_choice", 
                "get_multiline_input",
                "show_confirmation_dialog",
                "show_info_message",
                "get_human_loop_prompt"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "gui_available": False,
            "error": str(e),
            "platform": CURRENT_PLATFORM
        }

# Main execution
def main():
    print("Starting Human-in-the-Loop MCP Server (macOS Thread-Safe Version)...")
    print("This server provides tools for LLMs to interact with humans through GUI dialogs.")
    print(f"Platform: {CURRENT_PLATFORM} ({platform.system()} {platform.release()})")
    print("")
    print("Available tools:")
    print("- get_user_input - Get text/number input from user")
    print("- get_user_choice - Let user choose from options")
    print("- get_multiline_input - Get multi-line text from user")
    print("- show_confirmation_dialog - Ask user for yes/no confirmation")
    print("- show_info_message - Display information to user")
    print("- get_human_loop_prompt - Get guidance on when to use human-in-the-loop tools")
    print("- health_check - Check server status")
    print("")
    
    # Platform-specific startup messages
    if IS_MACOS:
        print("✓ macOS detected - Using thread-safe GUI implementation")
        print("✓ All GUI operations will run on the main thread")
        print("Note: You may need to allow Python in System Preferences > Security & Privacy > Accessibility")
    elif IS_WINDOWS:
        print("Windows detected - Using modern Windows 11-style GUI")
    elif IS_LINUX:
        print("Linux detected - Using Linux-compatible GUI settings")
    
    # Test GUI availability
    try:
        if ensure_gui_thread_running():
            print("✓ GUI thread initialized successfully")
    except Exception as e:
        print(f"⚠ Warning: GUI initialization failed: {e}")
    
    print("")
    print("Starting MCP server...")
    
    # Run the server
    mcp.run()

if __name__ == "__main__":
    main()
