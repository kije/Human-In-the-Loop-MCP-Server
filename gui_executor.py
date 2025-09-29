#!/usr/bin/env python3
"""
GUI Executor for Human-in-the-Loop MCP Server
This file should be saved as 'gui_executor.py' in the same directory as the main server file.
Features modern UI styling with platform-specific themes.
"""

import sys
import pickle
import tkinter as tk
from tkinter import ttk
import platform
import os

CURRENT_PLATFORM = platform.system().lower()
IS_WINDOWS = CURRENT_PLATFORM == 'windows'
IS_MACOS = CURRENT_PLATFORM == 'darwin'
IS_LINUX = CURRENT_PLATFORM == 'linux'

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

def create_modern_button(parent, text, command, button_type="primary", theme_colors=None):
    """Create a modern styled button with hover effects"""
    if theme_colors is None:
        theme_colors = get_theme_colors()
    
    if button_type == "primary":
        bg_color = theme_colors["accent_color"]
        fg_color = "#FFFFFF"
        hover_color = theme_colors["accent_hover"]
    else:  # secondary
        bg_color = theme_colors["bg_secondary"]
        fg_color = theme_colors["fg_primary"]
        hover_color = theme_colors["bg_accent"]
    
    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg_color,
        fg=fg_color,
        font=get_system_font(),
        relief="flat",
        borderwidth=0,
        padx=20,
        pady=8,
        cursor="hand2" if IS_WINDOWS else "pointinghand"
    )
    
    # Add hover effects
    def on_enter(e):
        button.configure(bg=hover_color)
    
    def on_leave(e):
        button.configure(bg=bg_color)
    
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    
    return button

def apply_modern_style(widget, widget_type="default", theme_colors=None):
    """Apply modern styling to tkinter widgets"""
    if theme_colors is None:
        theme_colors = get_theme_colors()
    
    try:
        if widget_type == "frame":
            widget.configure(
                bg=theme_colors["bg_primary"],
                relief="flat",
                borderwidth=0
            )
        elif widget_type == "label":
            widget.configure(
                bg=theme_colors["bg_primary"],
                fg=theme_colors["fg_primary"],
                font=get_system_font(),
                anchor="w"
            )
        elif widget_type == "title_label":
            widget.configure(
                bg=theme_colors["bg_primary"],
                fg=theme_colors["fg_primary"],
                font=get_title_font(),
                anchor="w"
            )
        elif widget_type == "listbox":
            widget.configure(
                bg=theme_colors["bg_primary"],
                fg=theme_colors["fg_primary"],
                selectbackground=theme_colors["selection_bg"],
                selectforeground=theme_colors["selection_fg"],
                relief="solid",
                borderwidth=1,
                highlightthickness=1,
                highlightcolor=theme_colors["accent_color"],
                highlightbackground=theme_colors["border_color"],
                font=get_system_font(),
                activestyle="none"
            )
        elif widget_type == "text":
            widget.configure(
                bg=theme_colors["bg_primary"],
                fg=theme_colors["fg_primary"],
                selectbackground=theme_colors["selection_bg"],
                selectforeground=theme_colors["selection_fg"],
                relief="solid",
                borderwidth=1,
                highlightthickness=1,
                highlightcolor=theme_colors["accent_color"],
                highlightbackground=theme_colors["border_color"],
                font=get_text_font(),
                wrap="word",
                padx=12,
                pady=8
            )
        elif widget_type == "entry":
            widget.configure(
                bg=theme_colors["bg_primary"],
                fg=theme_colors["fg_primary"],
                relief="solid",
                borderwidth=1,
                highlightthickness=1,
                highlightcolor=theme_colors["accent_color"],
                highlightbackground=theme_colors["border_color"],
                insertbackground=theme_colors["accent_color"],
                font=get_system_font()
            )
        elif widget_type == "scrollbar":
            widget.configure(
                bg=theme_colors["bg_secondary"],
                troughcolor=theme_colors["bg_accent"],
                activebackground=theme_colors["accent_hover"],
                relief="flat",
                borderwidth=0,
                highlightthickness=0
            )
    except Exception:
        pass  # Ignore styling errors on different platforms

def bring_window_to_front(window):
    """Aggressively bring window to foreground and get user attention"""
    try:
        if IS_MACOS:
            # macOS specific - multiple approaches for reliability
            try:
                # Set window to topmost
                window.attributes('-topmost', True)
                window.lift()
                window.focus_force()
                
                # Use AppleScript to activate Python and bring to front
                import subprocess
                
                # First, activate Python application
                subprocess.run([
                    'osascript', '-e',
                    f'tell application "System Events" to set frontmost of first process whose unix id is {os.getpid()} to true'
                ], check=False, capture_output=True, timeout=0.5)
                
                # Also try to activate by name (backup method)
                subprocess.run([
                    'osascript', '-e',
                    'tell application "Python" to activate'
                ], check=False, capture_output=True, timeout=0.5)
                
                # Play system sound to alert user
                subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'], 
                             check=False, capture_output=True, timeout=0.5)
            except:
                pass
                
        elif IS_WINDOWS:
            # Windows specific - use ctypes for more aggressive focusing
            try:
                import ctypes
                user32 = ctypes.windll.user32
                
                # Get window handle
                hwnd = user32.GetForegroundWindow()
                
                # Flash the window to get attention
                user32.FlashWindow(hwnd, True)
                
                # Set as foreground window
                user32.SetForegroundWindow(hwnd)
                user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE = 3
                user32.ShowWindow(hwnd, 1)  # SW_NORMAL = 1
            except:
                pass
            
            # Fallback Tkinter methods
            window.attributes('-topmost', True)
            window.lift()
            window.focus_force()
            window.bell()  # System beep
            
        else:  # Linux
            # Linux window manager activation
            window.attributes('-topmost', True)
            window.lift()
            window.focus_force()
            window.bell()  # System beep
            
            try:
                # Try wmctrl if available
                import subprocess
                subprocess.run(['wmctrl', '-a', window.title()], 
                             check=False, capture_output=True, timeout=0.5)
            except:
                pass
        
        # Universal additional measures
        window.update()
        window.update_idletasks()
        window.deiconify()  # Ensure window is not minimized
        
        # Briefly remove and re-add topmost to ensure it takes effect
        window.after(100, lambda: window.attributes('-topmost', False))
        window.after(200, lambda: window.attributes('-topmost', True))
        
    except Exception as e:
        # Even if advanced methods fail, try basic approach
        try:
            window.attributes('-topmost', True)
            window.lift()
            window.focus_force()
        except:
            pass

def configure_modern_window(window):
    """Apply modern window styling and bring to foreground"""
    theme_colors = get_theme_colors()
    
    try:
        window.configure(bg=theme_colors["bg_primary"])
        
        if IS_WINDOWS:
            try:
                window.attributes('-alpha', 0.98)  # Slight transparency
            except:
                pass
        
        # Aggressively bring window to foreground
        bring_window_to_front(window)
        
    except Exception:
        pass

class ModernInputDialog:
    def __init__(self, title, prompt, default_value="", input_type="text"):
        self.result = None
        self.input_type = input_type
        
        # Get theme colors
        self.theme_colors = get_theme_colors()
        
        # Create root window
        self.root = tk.Tk()
        self.root.title(title)
        self.root.resizable(False, False)
        
        # Apply modern window styling
        configure_modern_window(self.root)
        
        # Set size based on platform
        if IS_WINDOWS:
            self.root.geometry("420x280")
        else:
            self.root.geometry("400x260")
        
        self.center_window()
        
        # Additional focus attempts after window is created
        self.root.after(10, lambda: bring_window_to_front(self.root))
        self.root.after(100, lambda: self.root.focus_force())
        self.root.after(200, lambda: self.root.lift())
        
        # Create the main frame with padding
        main_frame = tk.Frame(self.root)
        apply_modern_style(main_frame, "frame", self.theme_colors)
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)
        
        # Title label
        title_label = tk.Label(main_frame, text=title)
        apply_modern_style(title_label, "title_label", self.theme_colors)
        title_label.pack(fill="x", pady=(0, 8))
        
        # Prompt label
        prompt_label = tk.Label(
            main_frame,
            text=prompt,
            wraplength=350,
            justify="left"
        )
        prompt_label.configure(
            bg=self.theme_colors["bg_primary"],
            fg=self.theme_colors["fg_secondary"],
            font=get_system_font(),
            anchor="w"
        )
        prompt_label.pack(fill="x", pady=(0, 20))
        
        # Input field frame
        input_frame = tk.Frame(main_frame)
        apply_modern_style(input_frame, "frame", self.theme_colors)
        input_frame.pack(fill="x", pady=(0, 24))
        
        # Entry widget with modern styling
        self.entry = tk.Entry(input_frame)
        apply_modern_style(self.entry, "entry", self.theme_colors)
        self.entry.pack(fill="x", ipady=8, ipadx=12)
        
        if default_value:
            self.entry.insert(0, default_value)
            self.entry.select_range(0, tk.END)
        
        # Button frame
        button_frame = tk.Frame(main_frame)
        apply_modern_style(button_frame, "frame", self.theme_colors)
        button_frame.pack(fill="x")
        
        # Create modern buttons
        ok_button = create_modern_button(
            button_frame, "OK", self.ok_clicked, "primary", self.theme_colors
        )
        ok_button.pack(side=tk.RIGHT, padx=(8, 0))
        
        cancel_button = create_modern_button(
            button_frame, "Cancel", self.cancel_clicked, "secondary", self.theme_colors
        )
        cancel_button.pack(side=tk.RIGHT)
        
        # Handle window close and keyboard shortcuts
        self.root.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
        self.root.bind('<Return>', lambda e: self.ok_clicked())
        self.root.bind('<Escape>', lambda e: self.cancel_clicked())
        
        # Focus on entry
        self.entry.focus_set()
        
        # Run the main loop
        self.root.mainloop()
    
    def center_window(self):
        """Center the dialog window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        
        if IS_MACOS:
            y = max(50, y - 50)
        elif IS_WINDOWS:
            y = max(30, y - 30)
            
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
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

class ModernConfirmationDialog:
    def __init__(self, title, message):
        self.result = False
        
        # Get theme colors
        self.theme_colors = get_theme_colors()
        
        self.root = tk.Tk()
        self.root.title(title)
        self.root.resizable(False, False)
        
        # Apply modern window styling
        configure_modern_window(self.root)
        
        # Set size based on platform
        if IS_WINDOWS:
            self.root.geometry("440x220")
        else:
            self.root.geometry("420x200")
        
        self.center_window()
        
        # Additional focus attempts after window is created
        self.root.after(10, lambda: bring_window_to_front(self.root))
        self.root.after(100, lambda: self.root.focus_force())
        self.root.after(200, lambda: self.root.lift())
        
        # Create the main frame
        main_frame = tk.Frame(self.root)
        apply_modern_style(main_frame, "frame", self.theme_colors)
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)
        
        # Title label
        title_label = tk.Label(main_frame, text=title)
        apply_modern_style(title_label, "title_label", self.theme_colors)
        title_label.pack(fill="x", pady=(0, 12))
        
        # Message label
        message_label = tk.Label(
            main_frame,
            text=message,
            wraplength=370,
            justify="left"
        )
        message_label.configure(
            bg=self.theme_colors["bg_primary"],
            fg=self.theme_colors["fg_secondary"],
            font=get_system_font(),
            anchor="w"
        )
        message_label.pack(fill="x", pady=(0, 24))
        
        # Button frame
        button_frame = tk.Frame(main_frame)
        apply_modern_style(button_frame, "frame", self.theme_colors)
        button_frame.pack(fill="x")
        
        # Create modern buttons
        yes_button = create_modern_button(
            button_frame, "Yes", self.yes_clicked, "primary", self.theme_colors
        )
        yes_button.pack(side=tk.RIGHT, padx=(8, 0))
        
        no_button = create_modern_button(
            button_frame, "No", self.no_clicked, "secondary", self.theme_colors
        )
        no_button.pack(side=tk.RIGHT)
        
        # Handle window close and keyboard shortcuts
        self.root.protocol("WM_DELETE_WINDOW", self.no_clicked)
        self.root.bind('<Return>', lambda e: self.yes_clicked())
        self.root.bind('<Escape>', lambda e: self.no_clicked())
        
        # Focus on No button by default (safer)
        no_button.focus_set()
        
        self.root.mainloop()
    
    def center_window(self):
        """Center the dialog window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        
        if IS_MACOS:
            y = max(50, y - 50)
        elif IS_WINDOWS:
            y = max(30, y - 30)
            
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def yes_clicked(self):
        self.result = True
        self.root.quit()
        self.root.destroy()
    
    def no_clicked(self):
        self.result = False
        self.root.quit()
        self.root.destroy()

class ModernInfoDialog:
    def __init__(self, title, message):
        self.result = True
        
        # Get theme colors
        self.theme_colors = get_theme_colors()
        
        self.root = tk.Tk()
        self.root.title(title)
        self.root.resizable(False, False)
        
        # Apply modern window styling
        configure_modern_window(self.root)
        
        # Set size based on platform
        if IS_WINDOWS:
            self.root.geometry("420x200")
        else:
            self.root.geometry("400x180")
        
        self.center_window()
        
        # Additional focus attempts after window is created
        self.root.after(10, lambda: bring_window_to_front(self.root))
        self.root.after(100, lambda: self.root.focus_force())
        self.root.after(200, lambda: self.root.lift())
        
        # Create the main frame
        main_frame = tk.Frame(self.root)
        apply_modern_style(main_frame, "frame", self.theme_colors)
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)
        
        # Title label
        title_label = tk.Label(main_frame, text=title)
        apply_modern_style(title_label, "title_label", self.theme_colors)
        title_label.pack(fill="x", pady=(0, 12))
        
        # Message label
        message_label = tk.Label(
            main_frame,
            text=message,
            wraplength=350,
            justify="left"
        )
        message_label.configure(
            bg=self.theme_colors["bg_primary"],
            fg=self.theme_colors["fg_secondary"],
            font=get_system_font(),
            anchor="w"
        )
        message_label.pack(fill="x", pady=(0, 24))
        
        # Button frame
        button_frame = tk.Frame(main_frame)
        apply_modern_style(button_frame, "frame", self.theme_colors)
        button_frame.pack(fill="x")
        
        # Create modern OK button
        ok_button = create_modern_button(
            button_frame, "OK", self.ok_clicked, "primary", self.theme_colors
        )
        ok_button.pack(side=tk.RIGHT)
        
        # Handle window close and keyboard shortcuts
        self.root.protocol("WM_DELETE_WINDOW", self.ok_clicked)
        self.root.bind('<Return>', lambda e: self.ok_clicked())
        self.root.bind('<Escape>', lambda e: self.ok_clicked())
        
        # Focus on OK button
        ok_button.focus_set()
        
        self.root.mainloop()
    
    def center_window(self):
        """Center the dialog window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        
        if IS_MACOS:
            y = max(50, y - 50)
        elif IS_WINDOWS:
            y = max(30, y - 30)
            
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def ok_clicked(self):
        self.result = True
        self.root.quit()
        self.root.destroy()

class ModernChoiceDialog:
    def __init__(self, title, prompt, choices, allow_multiple=False):
        self.result = None
        
        # Get theme colors
        self.theme_colors = get_theme_colors()
        
        self.root = tk.Tk()
        self.root.title(title)
        self.root.resizable(True, True)
        
        # Apply modern window styling
        configure_modern_window(self.root)
        
        # Set size based on platform
        if IS_MACOS:
            self.root.geometry("480x400")
        elif IS_WINDOWS:
            self.root.geometry("500x420")
        else:
            self.root.geometry("450x350")
        
        self.center_window()
        
        # Additional focus attempts after window is created
        self.root.after(10, lambda: bring_window_to_front(self.root))
        self.root.after(100, lambda: self.root.focus_force())
        self.root.after(200, lambda: self.root.lift())
        
        # Create the main frame with modern styling
        main_frame = tk.Frame(self.root)
        apply_modern_style(main_frame, "frame", self.theme_colors)
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Add modern title label
        title_label = tk.Label(main_frame, text=title)
        apply_modern_style(title_label, "title_label", self.theme_colors)
        title_label.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        
        # Add prompt label with modern styling
        prompt_label = tk.Label(
            main_frame,
            text=prompt,
            wraplength=450,
            justify="left"
        )
        prompt_label.configure(
            bg=self.theme_colors["bg_primary"],
            fg=self.theme_colors["fg_secondary"],
            font=get_system_font(),
            anchor="w"
        )
        prompt_label.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        # Create choice selection widget with modern container
        list_container = tk.Frame(main_frame)
        apply_modern_style(list_container, "frame", self.theme_colors)
        list_container.grid(row=2, column=0, sticky="nsew", pady=(0, 24))
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)
        
        # Modern listbox with styling
        self.listbox = tk.Listbox(
            list_container,
            selectmode=tk.MULTIPLE if allow_multiple else tk.SINGLE,
            height=8
        )
        apply_modern_style(self.listbox, "listbox", self.theme_colors)
        
        for choice in choices:
            self.listbox.insert(tk.END, choice)
        self.listbox.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        
        # Modern scrollbar
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.listbox.yview)
        apply_modern_style(scrollbar, "scrollbar", self.theme_colors)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        # Modern button frame
        button_frame = tk.Frame(main_frame)
        apply_modern_style(button_frame, "frame", self.theme_colors)
        button_frame.grid(row=3, column=0, sticky="ew")
        
        # Create modern buttons
        ok_button = create_modern_button(
            button_frame, "OK", self.ok_clicked, "primary", self.theme_colors
        )
        ok_button.pack(side=tk.RIGHT, padx=(8, 0))
        
        cancel_button = create_modern_button(
            button_frame, "Cancel", self.cancel_clicked, "secondary", self.theme_colors
        )
        cancel_button.pack(side=tk.RIGHT)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
        
        # Focus on listbox
        self.listbox.focus_set()
        if choices:
            self.listbox.selection_set(0)  # Select first item by default
        
        # Add keyboard shortcuts
        self.root.bind('<Return>', lambda e: self.ok_clicked())
        self.root.bind('<Escape>', lambda e: self.cancel_clicked())
        
        self.root.mainloop()
    
    def center_window(self):
        """Center the dialog window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        
        if IS_MACOS:
            y = max(50, y - 50)
        elif IS_WINDOWS:
            y = max(30, y - 30)
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
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

class ModernMultilineDialog:
    def __init__(self, title, prompt, default_value=""):
        self.result = None
        
        # Get theme colors
        self.theme_colors = get_theme_colors()
        
        self.root = tk.Tk()
        self.root.title(title)
        self.root.resizable(True, True)
        
        # Apply modern window styling
        configure_modern_window(self.root)
        
        # Set size based on platform
        if IS_MACOS:
            self.root.geometry("580x480")
        elif IS_WINDOWS:
            self.root.geometry("600x500")
        else:
            self.root.geometry("550x450")
        
        self.center_window()
        
        # Additional focus attempts after window is created
        self.root.after(10, lambda: bring_window_to_front(self.root))
        self.root.after(100, lambda: self.root.focus_force())
        self.root.after(200, lambda: self.root.lift())
        
        # Create the main frame with modern styling
        main_frame = tk.Frame(self.root)
        apply_modern_style(main_frame, "frame", self.theme_colors)
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Add modern title label
        title_label = tk.Label(main_frame, text=title)
        apply_modern_style(title_label, "title_label", self.theme_colors)
        title_label.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        
        # Add prompt label with modern styling
        prompt_label = tk.Label(
            main_frame,
            text=prompt,
            wraplength=520,
            justify="left"
        )
        prompt_label.configure(
            bg=self.theme_colors["bg_primary"],
            fg=self.theme_colors["fg_secondary"],
            font=get_system_font(),
            anchor="w"
        )
        prompt_label.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        # Create text widget container with modern styling
        text_container = tk.Frame(main_frame)
        apply_modern_style(text_container, "frame", self.theme_colors)
        text_container.grid(row=2, column=0, sticky="nsew", pady=(0, 24))
        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)
        
        # Modern text widget
        self.text_widget = tk.Text(text_container, height=12)
        apply_modern_style(self.text_widget, "text", self.theme_colors)
        self.text_widget.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        
        # Modern scrollbar for text widget
        text_scrollbar = tk.Scrollbar(text_container, orient="vertical", command=self.text_widget.yview)
        apply_modern_style(text_scrollbar, "scrollbar", self.theme_colors)
        text_scrollbar.grid(row=0, column=1, sticky="ns")
        self.text_widget.configure(yscrollcommand=text_scrollbar.set)
        
        # Set default value
        if default_value:
            self.text_widget.insert("1.0", default_value)
        
        # Modern button frame
        button_frame = tk.Frame(main_frame)
        apply_modern_style(button_frame, "frame", self.theme_colors)
        button_frame.grid(row=3, column=0, sticky="ew")
        
        # Create modern buttons
        ok_button = create_modern_button(
            button_frame, "OK", self.ok_clicked, "primary", self.theme_colors
        )
        ok_button.pack(side=tk.RIGHT, padx=(8, 0))
        
        cancel_button = create_modern_button(
            button_frame, "Cancel", self.cancel_clicked, "secondary", self.theme_colors
        )
        cancel_button.pack(side=tk.RIGHT)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.cancel_clicked)
        
        # Focus on text widget
        self.text_widget.focus_set()
        
        # Add keyboard shortcuts
        self.root.bind('<Control-Return>', lambda e: self.ok_clicked())
        self.root.bind('<Escape>', lambda e: self.cancel_clicked())
        
        self.root.mainloop()
    
    def center_window(self):
        """Center the dialog window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        
        if IS_MACOS:
            y = max(50, y - 50)
        elif IS_WINDOWS:
            y = max(30, y - 30)
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
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
        # Create the appropriate dialog with modern styling
        if dialog_type == "input":
            dialog = ModernInputDialog(
                dialog_params["title"], 
                dialog_params["prompt"],
                dialog_params.get("default_value", ""),
                dialog_params.get("input_type", "text")
            )
            result = dialog.result
            
        elif dialog_type == "confirmation":
            dialog = ModernConfirmationDialog(
                dialog_params["title"],
                dialog_params["message"]
            )
            result = dialog.result
            
        elif dialog_type == "info":
            dialog = ModernInfoDialog(
                dialog_params["title"],
                dialog_params["message"]
            )
            result = dialog.result
            
        elif dialog_type == "choice":
            dialog = ModernChoiceDialog(
                dialog_params["title"],
                dialog_params["prompt"],
                dialog_params["choices"],
                dialog_params.get("allow_multiple", False)
            )
            result = dialog.result
            
        elif dialog_type == "multiline":
            dialog = ModernMultilineDialog(
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
