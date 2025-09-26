#!/usr/bin/env python3
"""
Test with future times to confirm the fix works
"""

import sys
import os
from datetime import datetime
import pytz

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from events_agent.infra.date_parsing import parse_natural_range
from events_agent.infra.settings import settings

def test_future_times():
    """Test with times in the future"""
    print("🔍 TESTING WITH FUTURE TIMES")
    print("=" * 50)
    
    melb_tz = pytz.timezone(settings.default_tz)
    now_melb = datetime.now(melb_tz)
    
    print(f"Current Melbourne time: {now_melb.strftime('%I:%M %p')}")
    print()
    
    # Test with future times
    future_test_cases = [
        "5PM September 26",  # Today, but in the future
        "6PM today",         # Today, but in the future  
        "3PM September 27",  # Tomorrow at 3PM
        "3PM tomorrow",      # Tomorrow at 3PM
    ]
    
    for test_input in future_test_cases:
        print(f"Input: '{test_input}'")
        
        try:
            start_dt, end_dt = parse_natural_range(test_input, settings.default_tz)
            print(f"  Parsed: {start_dt.strftime('%A, %B %d at %I:%M %p')}")
            
            if start_dt > now_melb:
                print(f"  ✅ FUTURE event - This should work correctly")
            else:
                print(f"  ⚠️  PAST event")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_future_times()