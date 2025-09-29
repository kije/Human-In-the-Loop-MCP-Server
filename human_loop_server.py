#!/usr/bin/env python3
"""
Human-in-the-Loop MCP Server - macOS Compatible Version

This server provides tools for getting human input and choices through GUI dialogs.
Uses subprocess-based GUI execution for macOS compatibility.
"""

import asyncio
import json
import platform
import subprocess
import sys
import os
import pickle
import tempfile
from typing import List, Dict, Any, Optional, Literal
from pydantic import Field
from typing import Annotated

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

# GUI executor script that runs in a separate process
GUI_EXECUTOR_SCRIPT = '''
import sys
import pickle
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import platform

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
    else:
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

class ModernInputDialog:
    def __init__(self, parent, title, prompt, default_value="", input_type="text"):
        self.result = None
        self.input_type = input_type
        self.theme_colors = get_theme_colors()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        self.dialog.configure(bg=self.theme_colors["bg_primary"])
        if IS_MACOS:
            try:
                self.dialog.attributes('-topmost', True)
                self.dialog.lift()
                self.dialog.focus_force()
            except:
                pass
        elif IS_WINDOWS:
            self.dialog.attributes('-topmost', True)
        
        self.dialog.geometry("420x280" if IS_WINDOWS else "400x260")
        self.center_window()
        
        main_frame = tk.Frame(self.dialog, bg=self.theme_colors["bg_primary"])
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)
        
        tk.Label(main_frame, text=title, bg=self.theme_colors["bg_primary"],
                fg=self.theme_colors["fg_primary"], font=get_title_font(),
                anchor="w").pack(fill="x", pady=(0, 8))
        
        tk.Label(main_frame, text=prompt, bg=self.theme_colors["bg_primary"],
                fg=self.theme_colors["fg_secondary"], font=get_system_font(),
                wraplength=350, justify="left", anchor="w").pack(fill="x", pady=(0, 20))
        
        input_frame = tk.Frame(main_frame, bg=self.theme_colors["bg_primary"])
        input_frame.pack(fill="x", pady=(0, 24))
        
        self.entry = tk.Entry(input_frame, font=get_system_font(),
                             bg=self.theme_colors["bg_primary"],
                             fg=self.theme_colors["fg_primary"],
                             relief="solid", borderwidth=1)
        self.entry.pack(fill="x", ipady=8, ipadx=12)
        
        if default_value:
            self.entry.insert(0, default_value)
            self.entry.select_range(0, tk.END)
        
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
        
        self.entry.focus_set()
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
                self.dialog.attributes('-topmost', True)
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
                self.dialog.attributes('-topmost', True)
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
                self.dialog.attributes('-topmost', True)
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
                self.dialog.attributes('-topmost', True)
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

def execute_dialog(dialog_type, params):
    """Execute a dialog based on type and parameters"""
    root = tk.Tk()
    root.withdraw()
    
    if IS_MACOS:
        try:
            import subprocess
            subprocess.run([
                'osascript', '-e', 
                f'tell application "System Events" to set frontmost of first process whose unix id is {os.getpid()} to true'
            ], check=False, capture_output=True, timeout=1)
        except:
            pass
    
    result = None
    
    try:
        if dialog_type == "input":
            dialog = ModernInputDialog(root, params["title"], params["prompt"], 
                                     params.get("default_value", ""), params.get("input_type", "text"))
            result = dialog.result
        elif dialog_type == "choice":
            dialog = ChoiceDialog(root, params["title"], params["prompt"], 
                                params["choices"], params.get("allow_multiple", False))
            result = dialog.result
        elif dialog_type == "multiline":
            dialog = MultilineInputDialog(root, params["title"], params["prompt"], 
                                         params.get("default_value", ""))
            result = dialog.result
        elif dialog_type == "confirmation":
            dialog = ModernConfirmationDialog(root, params["title"], params["message"])
            result = dialog.result
        elif dialog_type == "info":
            dialog = ModernInfoDialog(root, params["title"], params["message"])
            result = dialog.result
    except Exception as e:
        result = {"error": str(e)}
    finally:
        try:
            root.quit()
            root.destroy()
        except:
            pass
    
    return result

if __name__ == "__main__":
    # Read parameters from stdin
    import os
    params_data = sys.stdin.buffer.read()
    params = pickle.loads(params_data)
    
    # Execute the dialog
    result = execute_dialog(params["dialog_type"], params["params"])
    
    # Write result to stdout
    sys.stdout.buffer.write(pickle.dumps(result))
    sys.stdout.flush()
'''

def run_gui_subprocess(dialog_type: str, params: dict) -> Any:
    """Run a GUI dialog in a subprocess where it can use the main thread"""
    try:
        # Prepare the parameters
        request = {
            "dialog_type": dialog_type,
            "params": params
        }
        
        # Create a subprocess to run the GUI
        process = subprocess.Popen(
            [sys.executable, "-c", GUI_EXECUTOR_SCRIPT],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Send parameters and get result
        stdout, stderr = process.communicate(input=pickle.dumps(request))
        
        if process.returncode != 0:
            if stderr:
                raise RuntimeError(f"GUI subprocess error: {stderr.decode()}")
            return None
        
        # Parse the result
        result = pickle.loads(stdout)
        
        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(f"GUI error: {result['error']}")
        
        return result
        
    except Exception as e:
        print(f"Error in GUI subprocess: {e}")
        return None

# MCP Tools

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
        
        # Run dialog in subprocess
        params = {
            "title": title,
            "prompt": prompt,
            "default_value": default_value,
            "input_type": input_type
        }
        
        result = await asyncio.get_event_loop().run_in_executor(
            None, run_gui_subprocess, "input", params
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
        
        params = {
            "title": title,
            "prompt": prompt,
            "choices": choices,
            "allow_multiple": allow_multiple
        }
        
        result = await asyncio.get_event_loop().run_in_executor(
            None, run_gui_subprocess, "choice", params
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
        
        params = {
            "title": title,
            "prompt": prompt,
            "default_value": default_value
        }
        
        result = await asyncio.get_event_loop().run_in_executor(
            None, run_gui_subprocess, "multiline", params
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
        
        params = {
            "title": title,
            "message": message
        }
        
        result = await asyncio.get_event_loop().run_in_executor(
            None, run_gui_subprocess, "confirmation", params
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
        
        params = {
            "title": title,
            "message": message
        }
        
        result = await asyncio.get_event_loop().run_in_executor(
            None, run_gui_subprocess, "info", params
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

@mcp.prompt()
async def get_human_loop_prompt() -> Dict[str, str]:
    """Get prompting guidance for LLMs on when and how to use human-in-the-loop tools."""
    return {
        "main_prompt": """
You have access to Human-in-the-Loop tools that allow you to interact directly with users through GUI dialogs. Use these tools strategically to enhance task completion and user experience.

**WHEN TO USE HUMAN-IN-THE-LOOP TOOLS:**

1. **Ambiguous Requirements** - When user instructions are unclear or could have multiple interpretations
2. **Decision Points** - When you need user preference between valid alternatives
3. **Creative Input** - For subjective choices like design, content style, or personal preferences
4. **Sensitive Operations** - Before executing potentially destructive or irreversible actions
5. **Missing Information** - When you need specific details not provided in the original request
6. **Quality Feedback** - To get user validation on intermediate results before proceeding
7. **Error Handling** - When encountering issues that require user guidance to resolve

**AVAILABLE TOOLS:**
- `get_user_input` - Single-line text/number input (names, values, paths, etc.)
- `get_user_choice` - Multiple choice selection (pick from options)
- `get_multiline_input` - Long-form text (descriptions, code, documents)
- `show_confirmation_dialog` - Yes/No decisions (confirmations, approvals)
- `show_info_message` - Status updates and notifications

**BEST PRACTICES:**
- Ask specific, clear questions with context
- Provide helpful default values when possible
- Use confirmation dialogs before destructive actions
- Give status updates for long-running processes
- Offer meaningful choices rather than overwhelming options
- Be concise but informative in dialog prompts""",
        
        "usage_examples": """
**EXAMPLE SCENARIOS:**

1. **File Operations:**
   - "I'm about to delete 15 files. Should I proceed?" (confirmation)
   - "Enter the target directory path:" (input)
   - "Choose backup format: Full, Incremental, Differential" (choice)

2. **Content Creation:**
   - "What tone should I use: Professional, Casual, Friendly?" (choice)
   - "Please provide any specific requirements:" (multiline input)
   - "Content generated successfully!" (info message)

3. **Code Development:**
   - "Enter the API endpoint URL:" (input)
   - "Select framework: React, Vue, Angular, Vanilla JS" (choice)
   - "Review the generated code and provide feedback:" (multiline input)

4. **Data Processing:**
   - "Found 3 data formats. Which should I use?" (choice)
   - "Enter the date range (YYYY-MM-DD to YYYY-MM-DD):" (input)
   - "Processing complete. 1,250 records updated." (info message)""",
        
        "decision_framework": """
**DECISION FRAMEWORK FOR HUMAN-IN-THE-LOOP:**

ASK YOURSELF:
1. Is this decision subjective or preference-based? → USE CHOICE DIALOG
2. Do I need specific information not provided? → USE INPUT DIALOG  
3. Could this action cause problems if wrong? → USE CONFIRMATION DIALOG
4. Is this a long process the user should know about? → USE INFO MESSAGE
5. Do I need detailed explanation or content? → USE MULTILINE INPUT

AVOID OVERUSE:
- Don't ask for information already provided
- Don't seek confirmation for obviously safe operations
- Don't interrupt flow for trivial decisions
- Don't ask multiple questions when one comprehensive dialog would suffice""",
        
        "integration_tips": """
**INTEGRATION TIPS:**

1. **Workflow Integration:**
   Step 1: Analyze user request
   Step 2: Identify decision points and missing info
   Step 3: Use appropriate human-in-the-loop tools
   Step 4: Process user responses
   Step 5: Continue with enhanced information

2. **Error Recovery:**
   - If user cancels, gracefully explain and offer alternatives
   - Handle timeouts by providing default behavior
   - Always validate user input before proceeding

3. **Progressive Enhancement:**
   - Start with automated solutions
   - Add human input only where it adds clear value
   - Learn from user patterns to improve future automation"""
    }

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Check if the Human-in-the-Loop server is running and GUI is available."""
    try:
        # Test GUI availability by trying a simple operation
        test_params = {
            "title": "Health Check",
            "message": "Testing GUI availability..."
        }
        
        # Try to run a test dialog (but with a very short timeout)
        gui_test_success = False
        try:
            # We don't actually show the dialog, just test if subprocess works
            process = subprocess.Popen(
                [sys.executable, "-c", "import tkinter; print('OK')"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=2)
            gui_test_success = process.returncode == 0 and b'OK' in stdout
        except:
            gui_test_success = False
        
        return {
            "status": "healthy" if gui_test_success else "degraded",
            "gui_available": gui_test_success,
            "server_name": "Human-in-the-Loop Server (Subprocess Mode)",
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
                "get_human_loop_prompt",
                "health_check"
            ],
            "execution_mode": "subprocess",
            "note": "GUI operations run in separate processes for thread safety"
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
    print("Starting Human-in-the-Loop MCP Server (macOS Subprocess Mode)...")
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
        print("✓ macOS detected - Using subprocess mode for thread safety")
        print("✓ Each GUI dialog runs in its own process with main thread access")
        print("Note: You may need to allow Python in System Preferences > Security & Privacy > Accessibility")
    elif IS_WINDOWS:
        print("Windows detected - Using subprocess mode with Windows 11-style GUI")
    elif IS_LINUX:
        print("Linux detected - Using subprocess mode with Linux-compatible GUI")
    
    # Test GUI availability
    print("\nTesting GUI availability...")
    try:
        process = subprocess.Popen(
            [sys.executable, "-c", "import tkinter; print('OK')"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate(timeout=2)
        if process.returncode == 0 and b'OK' in stdout:
            print("✓ GUI system is available")
        else:
            print("⚠ GUI system may have issues")
    except Exception as e:
        print(f"⚠ Could not verify GUI availability: {e}")
    
    print("\nStarting MCP server...")
    
    # Run the server
    mcp.run()

if __name__ == "__main__":
    main()
