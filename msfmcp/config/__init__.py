#!/usr/bin/env python3

"""
Configuration file for MSFConsole MCP
This file contains all configurable settings for the MSFConsole MCP server.
"""

import os
import shutil
from typing import Dict, Any, List

# Find msfconsole and msfvenom in PATH
MSFCONSOLE_PATH = shutil.which("msfconsole") or "/usr/bin/msfconsole"
MSFVENOM_PATH = shutil.which("msfvenom") or "/usr/bin/msfvenom"

# Configuration dictionary
CONFIG: Dict[str, Any] = {
    # Metasploit Framework settings
    "metasploit": {
        "msfconsole_path": MSFCONSOLE_PATH,
        "msfvenom_path": MSFVENOM_PATH,
        "workspace": "default",  # Default Metasploit workspace
        "timeout": 30,  # Default timeout for metasploit commands (seconds) - reduced from 60
        "db_check_timeout": 10,  # Specific timeout for database checks (seconds)
        "retry_attempts": 2,     # Number of retries for failed commands
        "retry_delay": 1,        # Delay between retries (seconds)
    },
    
    # Security settings
    "security": {
        "command_timeout": 60,  # Maximum time (seconds) a command can run - reduced from 120
        "disallowed_modules": [  # Potentially dangerous modules to block
            "exploit/windows/smb/psexec",
            "exploit/multi/handler",
            # Add other dangerous modules as needed
        ],
        "validate_commands": True,  # Whether to validate commands before running
    },
    
    # Output settings
    "output": {
        "max_output_length": 50000,  # Maximum length of command output to return
        "truncation_message": "\n[... Output truncated due to length. Full output in Metasploit logs ...]\n",
    },
    
    # Server settings
    "server": {
        "host": "localhost",
        "port": 8080,
        "debug": True,
        "log_level": "INFO",
    },
    
    # Documentation settings
    "docs": {
        "path": os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp-documentation"),
        "enable_docs": True,
    },
    
    # Error handling settings
    "error_handling": {
        "suppress_db_errors": True,  # Continue without database if db_status fails
        "db_error_message": "Database connection not available, some functionality will be limited.",
        "show_stack_traces": False,  # Whether to include stack traces in error messages
    },
    
    # Progress reporting settings
    "progress": {
        "default_steps": 100,  # Default number of steps for progress reporting
        "report_interval": 10,  # Report progress every N%
    },
}

# Python compatibility fixes
PY_COMPATIBILITY_FIXES = {
    "asyncio_fix": True,  # Enable fixes for asyncio in Python 3.12+
    "context_fixes": True,  # Enable fixes for context-related issues
    "progress_compatibility": True,  # Enable compatibility mode for progress reporting
}

# Define fallback messages for common errors
ERROR_MESSAGES = {
    "db_timeout": "Database check timed out. Continuing without database connection.",
    "msf_timeout": "Metasploit command timed out. This could be due to system load or configuration issues.",
    "command_failed": "Command execution failed. Please verify Metasploit installation and try again.",
    "version_check_failed": "Could not determine Metasploit version. Continuing with limited functionality.",
}

# Verify the configuration at import time
def verify_config():
    """Verify and normalize configuration"""
    # Check for invalid timeouts
    if CONFIG["metasploit"]["timeout"] <= 0:
        print("Warning: Invalid timeout value, setting to default 30 seconds")
        CONFIG["metasploit"]["timeout"] = 30
    
    # Check for invalid retry settings
    if CONFIG["metasploit"]["retry_attempts"] < 0:
        CONFIG["metasploit"]["retry_attempts"] = 0
    
    # Ensure metasploit paths exist or warn
    if not os.path.exists(CONFIG["metasploit"]["msfconsole_path"]):
        print(f"Warning: msfconsole not found at {CONFIG['metasploit']['msfconsole_path']}")
    
    if not os.path.exists(CONFIG["metasploit"]["msfvenom_path"]):
        print(f"Warning: msfvenom not found at {CONFIG['metasploit']['msfvenom_path']}")

# Run verification at import time
verify_config()
