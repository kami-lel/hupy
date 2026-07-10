"""
conftest.py

shared pytest fixtures for `should_run_module` tests
"""

import sys
from pathlib import Path

# make the shared config fixture loader importable from here
sys.path.insert(0, str(Path(__file__).parent.parent / "fixtures"))
