#!/usr/bin/env python3
"""
Simple launcher script for Calendar Agent
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Now import and run the main module
if __name__ == "__main__":
    from events_agent.main import main
    main()
