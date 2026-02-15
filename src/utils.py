import sys
from pathlib import Path

def get_base_path():
    """Get the base path for resources, handling both dev and PyInstaller environments."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        # If --onedir, sys.executable is the exe path.
        # If --onefile, sys._MEIPASS is the temp folder.
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        else:
            return Path(sys.executable).parent
    else:
        # Running from source
        # Calculate root from src/utils.py -> parent -> parent
        return Path(__file__).parent.parent
