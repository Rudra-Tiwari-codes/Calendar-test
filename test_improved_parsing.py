#!/usr/bin/env python3
"""
Test the improved date parsing that handles past times
"""

import sys
import os
from datetime import datetime
import pytz

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from events_agent.infra.date_parsing import parse_natural_range
from events_agent.infra.settings import settings

def test_improved_parsing():
    """Test the improved parsing that handles past times"""
    print("🔍 TESTING IMPROVED PAST TIME HANDLING")
    print("=" * 50)
    
    melb_tz = pytz.timezone(settings.default_tz)
    now_melb = datetime.now(melb_tz)
    
    print(f"Current Melbourne time: {now_melb.strftime('%A, %B %d at %I:%M %p')}")
    print()
    
    # Test cases that would be in the past
    test_cases = [
        "3PM September 26",     # Today, but past time
        "2PM September 26",     # Today, but past time  
        "September 26 1PM",     # Today, different format
        "today 2PM",            # Today, but past
        "Monday 3PM",           # This Monday (if past, should go to next Monday)
        "Friday 2PM",           # This Friday (if past, should go to next Friday)
    ]
    
    for test_input in test_cases:
        print(f"Input: '{test_input}'")
        
        try:
            start_dt, end_dt = parse_natural_range(test_input, settings.default_tz)
            print(f"  Parsed: {start_dt.strftime('%A, %B %d at %I:%M %p')}")
            
            if start_dt > now_melb:
                print(f"  ✅ FUTURE event (moved forward)")
            else:
                print(f"  ⚠️  Still in the past")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_improved_parsing()