#!/usr/bin/env python3
"""
Human-in-the-Loop MCP Server - macOS Compatible Version

This server provides tools for getting human input and choices through GUI dialogs.
Uses external subprocess execution for macOS thread safety.
"""

import asyncio
import json
import platform
import subprocess
import sys
import os
import pickle
from pathlib import Path
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

# Path to the GUI executor file
GUI_EXECUTOR_PATH = Path(__file__).parent / "gui_executor.py"

def run_gui_subprocess(dialog_type: str, params: dict) -> Any:
    """Run a GUI dialog in a subprocess where it can use the main thread"""
    try:
        # Check if gui_executor.py exists
        if not GUI_EXECUTOR_PATH.exists():
            raise FileNotFoundError(
                f"GUI executor file not found at {GUI_EXECUTOR_PATH}. "
                "Please ensure gui_executor.py is in the same directory as this server file."
            )
        
        # Prepare the parameters
        request = {
            "dialog_type": dialog_type,
            "params": params
        }
        
        # Create a subprocess to run the GUI executor
        process = subprocess.Popen(
            [sys.executable, str(GUI_EXECUTOR_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Send parameters and get result
        stdout, stderr = process.communicate(input=pickle.dumps(request))
        
        if process.returncode != 0:
            if stderr:
                error_msg = stderr.decode()
                # Check if it's an NSException error
                if "NSInternalInconsistencyException" in error_msg:
                    raise RuntimeError(
                        "macOS GUI thread error. Please ensure gui_executor.py is properly installed "
                        "and Python has accessibility permissions in System Preferences."
                    )
                raise RuntimeError(f"GUI subprocess error: {error_msg}")
            return None
        
        # Parse the result
        result = pickle.loads(stdout)
        
        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(f"GUI error: {result['error']}")
        
        return result
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Error in GUI subprocess: {e}")
        return None

# MCP Tools

@mcp.tool()
async def get_user_input(
    title: Annotated[str, Field(description="Title of the input dialog window")],
    prompt: Annotated[str, Field(description="The prompt to show to the user")],
    default_value: Annotated[str, Field(description="Default value to pre-fill the input with")] = "",
    input_type: Annotated[Literal["text", "integer", "float"], Field(description="Type of input expected")] = "text",
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Create an input dialog window for the user to enter text, numbers, or other data.
    
    Opens a GUI dialog box where the user can input information that the LLM needs.
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
    
    Opens a GUI dialog box with a list of choices where the user can select
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
    prompt: Annotated[str, Field(description="The prompt to show to the user")],
    default_value: Annotated[str, Field(description="Default text to pre-fill in the text area")] = "",
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Create a multi-line text input dialog for the user to enter longer text content.
    
    Opens a GUI dialog box with a multi-line text area where the user can input text. 
    Perfect for getting detailed descriptions, code, or long-form content.
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
    Shows a confirmation dialog with Yes/No buttons.
    
    Displays a confirmation dialog to the user.
    Perfect for getting approval or attention before proceeding with an action.
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
   - "Content generated successfully!" (info message)""",
        
        "decision_framework": """
**DECISION FRAMEWORK FOR HUMAN-IN-THE-LOOP:**

ASK YOURSELF:
1. Is this decision subjective or preference-based? → USE CHOICE DIALOG
2. Do I need specific information not provided? → USE INPUT DIALOG  
3. Could this action cause problems if wrong? → USE CONFIRMATION DIALOG
4. Is this a long process the user should know about? → USE INFO MESSAGE
5. Do I need detailed explanation or content? → USE MULTILINE INPUT"""
    }

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Check if the Human-in-the-Loop server is running and GUI is available."""
    try:
        # Check if GUI executor file exists
        gui_executor_exists = GUI_EXECUTOR_PATH.exists()
        
        # Test GUI availability
        gui_test_success = False
        if gui_executor_exists:
            try:
                # Test if we can import tkinter in a subprocess
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
            "status": "healthy" if (gui_executor_exists and gui_test_success) else "degraded",
            "gui_available": gui_test_success,
            "gui_executor_found": gui_executor_exists,
            "gui_executor_path": str(GUI_EXECUTOR_PATH),
            "server_name": "Human-in-the-Loop Server (External Subprocess Mode)",
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
            "execution_mode": "external_subprocess",
            "note": "GUI operations run in separate process files for maximum thread safety"
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
    print("Starting Human-in-the-Loop MCP Server (macOS External Subprocess Mode)...")
    print("This server provides tools for LLMs to interact with humans through GUI dialogs.")
    print(f"Platform: {CURRENT_PLATFORM} ({platform.system()} {platform.release()})")
    print("")
    
    # Check for gui_executor.py
    if not GUI_EXECUTOR_PATH.exists():
        print("⚠️  WARNING: gui_executor.py not found!")
        print(f"   Please ensure gui_executor.py is in: {GUI_EXECUTOR_PATH.parent}")
        print("   Download it from the project repository or create it from the provided code.")
        print("")
    else:
        print("✓ GUI executor file found")
    
    print("\nAvailable tools:")
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
        print("✓ macOS detected - Using external subprocess mode for absolute thread safety")
        print("✓ Each GUI dialog runs in a separate process with guaranteed main thread access")
        print("\nIMPORTANT: You may need to:")
        print("1. Allow Python in System Preferences > Security & Privacy > Accessibility")
        print("2. Ensure both human_loop_server.py and gui_executor.py are in the same directory")
    elif IS_WINDOWS:
        print("Windows detected - Using external subprocess mode")
    elif IS_LINUX:
        print("Linux detected - Using external subprocess mode")
    
    # Test GUI availability
    if GUI_EXECUTOR_PATH.exists():
        print("\nTesting GUI availability...")
        try:
            process = subprocess.Popen(
                [sys.executable, "-c", "import tkinter; print('OK')"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=2)
            if process.returncode == 0 and b'OK' in stdout:
                print("✓ GUI system is available and working")
            else:
                print("⚠ GUI system may have issues")
                if stderr:
                    print(f"  Error: {stderr.decode()[:200]}")
        except Exception as e:
            print(f"⚠ Could not verify GUI availability: {e}")
    
    print("\nStarting MCP server...")
    print("Ready to handle GUI requests through external subprocess execution.")
    print("")
    
    # Run the server
    mcp.run()

if __name__ == "__main__":
    main()
