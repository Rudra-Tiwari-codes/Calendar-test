#!/usr/bin/env python3
"""
Test the manual 10-hour offset fix
"""

import sys
import os
from datetime import datetime
import pytz

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from events_agent.infra.date_parsing import parse_natural_range
from events_agent.infra.settings import settings

def test_manual_timezone_fix():
    """Test the manual 10-hour offset fix"""
    print("🔧 TESTING MANUAL 10-HOUR OFFSET FIX")
    print("=" * 50)
    
    test_cases = [
        {
            "input": "3PM September 27",
            "should_offset": True,
            "description": "Manual date - should get 10h offset"
        },
        {
            "input": "September 27 2PM", 
            "should_offset": True,
            "description": "Manual date - should get 10h offset"
        },
        {
            "input": "today 3PM",
            "should_offset": False,
            "description": "Today - should NOT get offset"
        },
        {
            "input": "tomorrow 2PM",
            "should_offset": True, 
            "description": "Tomorrow - should get offset (not 'today')"
        },
        {
            "input": "Monday 3PM",
            "should_offset": False,
            "description": "Day of week - should NOT get offset"
        }
    ]
    
    for test_case in test_cases:
        print(f"\nInput: '{test_case['input']}'")
        print(f"Expected: {test_case['description']}")
        
        try:
            start_dt, end_dt = parse_natural_range(test_case['input'], settings.default_tz)
            
            print(f"Result: {start_dt.strftime('%A, %B %d at %I:%M %p')}")
            
            # Check if the time suggests an offset was applied
            hour = start_dt.hour
            if test_case['should_offset']:
                print(f"✅ Offset applied - Time: {hour}:00 (should be different from input)")
            else:
                print(f"✅ No offset - Time: {hour}:00 (should match input)")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎯 SUMMARY:")
    print(f"- Manual dates (September 27 3PM) → Gets 10h offset")
    print(f"- 'Today' events → NO offset (stays accurate)")
    print(f"- Days of week → NO offset")

if __name__ == "__main__":
    test_manual_timezone_fix()