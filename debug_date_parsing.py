#!/usr/bin/env python3
"""
Debug script to test date parsing with specific inputs
"""

import sys
import os
from datetime import datetime
import pytz

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from events_agent.infra.date_parsing import parse_natural_range, parse_natural_datetime
from events_agent.infra.settings import settings

def test_specific_input():
    """Test the specific input that's causing issues"""
    print("🔍 Testing date parsing for '3PM September 26'")
    print(f"Current date: {datetime.now()}")
    print(f"Default timezone: {settings.default_tz}")
    
    # Test the exact input
    test_input = "3PM September 26"
    print(f"\nTesting input: '{test_input}'")
    
    try:
        # Test single date parsing
        result = parse_natural_datetime(test_input, settings.default_tz)
        print(f"Single datetime result: {result}")
        print(f"Timezone: {result.tzinfo}")
        print(f"Formatted: {result.strftime('%A, %B %d at %I:%M %p')}")
        
        # Test range parsing
        start_dt, end_dt = parse_natural_range(test_input, settings.default_tz)
        print(f"\nRange parsing result:")
        print(f"Start: {start_dt}")
        print(f"End: {end_dt}")
        print(f"Start formatted: {start_dt.strftime('%A, %B %d at %I:%M %p')}")
        print(f"End formatted: {end_dt.strftime('%A, %B %d at %I:%M %p')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test other variations
    variations = [
        "September 26 3PM",
        "Sep 26 3PM", 
        "September 26th 3PM",
        "Thursday September 26 3PM",
        "September 26 15:00",
        "today 3PM",
        "tomorrow 3PM"
    ]
    
    print("\n🔍 Testing variations:")
    for variation in variations:
        try:
            start_dt, end_dt = parse_natural_range(variation, settings.default_tz)
            print(f"✅ '{variation}' -> {start_dt.strftime('%A, %B %d at %I:%M %p')} - {end_dt.strftime('%I:%M %p')}")
        except Exception as e:
            print(f"❌ '{variation}' failed: {e}")

if __name__ == "__main__":
    test_specific_input()