"""
SO Intelligence Package Entry Point

Allows running: python -m so_intelligence <command>
"""

import sys

from .main import main

if __name__ == "__main__":
    sys.exit(main())
