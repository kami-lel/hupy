"""
conftest.py

shared pytest fixtures for TTG (triage tag gating) tests
"""

import sys
from pathlib import Path

# make the shared repo-prep fixture builder importable from here
sys.path.insert(0, str(Path(__file__).parent.parent / "fixtures"))
