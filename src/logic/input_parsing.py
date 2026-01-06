"""Utilities for parsing and cleaning user input."""
import re

def clean_pasted_path(path: str) -> str:
    """Clean a path string that might have been pasted from a terminal/shell."""
    if not path:
        return ""
    
    # Remove leading/trailing whitespace
    path = path.strip()
    
    # PowerShell style: & "C:\path\to\file"
    if path.startswith('&'):
        path = path[1:].strip()
        
    # Remove quotes (single or double) at start/end
    if (path.startswith('"') and path.endswith('"')) or (path.startswith("'") and path.endswith("'")):
        path = path[1:-1]
        
    # Remove any extra surrounding whitespace that might have been inside quotes
    path = path.strip()
    
    return path
