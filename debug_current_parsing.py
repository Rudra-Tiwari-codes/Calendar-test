#!/usr/bin/env python3
"""
Test the current date parsing behavior in detail
"""

import sys
import os
from datetime import datetime
import pytz

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from events_agent.infra.date_parsing import parse_natural_range, parse_natural_datetime
from events_agent.infra.settings import settings

def test_current_parsing():
    """Test the current date parsing behavior"""
    print("🔍 DETAILED DATE PARSING TEST")
    print("=" * 50)
    print(f"Current time: {datetime.now()}")
    print(f"Current date: September 26, 2025") 
    print(f"Default timezone: {settings.default_tz}")
    print()
    
    # Test the exact input that's problematic
    test_input = "3PM September 26"
    print(f"Testing input: '{test_input}'")
    print()
    
    try:
        # Test single datetime parsing
        result = parse_natural_datetime(test_input, settings.default_tz)
        print(f"Parsed datetime: {result}")
        print(f"Timezone: {result.tzinfo}")
        print(f"ISO format: {result.isoformat()}")
        print(f"Formatted display: {result.strftime('%A, %B %d at %I:%M %p')}")
        print()
        
        # Test range parsing
        start_dt, end_dt = parse_natural_range(test_input, settings.default_tz)
        print(f"Range start: {start_dt}")
        print(f"Range end: {end_dt}")
        print(f"Start ISO: {start_dt.isoformat()}")
        print(f"End ISO: {end_dt.isoformat()}")
        print(f"Start display: {start_dt.strftime('%A, %B %d at %I:%M %p')}")
        print(f"End display: {end_dt.strftime('%A, %B %d at %I:%M %p')}")
        print()
        
        # Check what this would look like when stored/retrieved from Google Calendar
        print("🔍 GOOGLE CALENDAR SIMULATION:")
        print("When stored in Google Calendar, this becomes:")
        
        # Convert to UTC (what Google Calendar would store)
        utc_start = start_dt.astimezone(pytz.UTC)
        utc_end = end_dt.astimezone(pytz.UTC)
        
        print(f"UTC Start: {utc_start.isoformat()}")
        print(f"UTC End: {utc_end.isoformat()}")
        
        # Simulate what Google Calendar API returns (with Z suffix)
        google_format_start = utc_start.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        google_format_end = utc_end.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        print(f"Google API returns: {google_format_start}")
        print(f"Google API returns: {google_format_end}")
        
        # Test our current display logic
        from datetime import datetime as dt
        display_dt = dt.fromisoformat(google_format_start.replace("Z", "+00:00"))
        melb_tz = pytz.timezone(settings.default_tz)
        display_local = display_dt.astimezone(melb_tz)
        
        print(f"After conversion back: {display_local.strftime('%A, %B %d at %I:%M %p')}")
        
        # Check if dates match
        if start_dt.date() == display_local.date() and start_dt.time() == display_local.time():
            print("✅ Round-trip conversion works correctly!")
        else:
            print("❌ Round-trip conversion has issues!")
            print(f"Original: {start_dt}")
            print(f"After round-trip: {display_local}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_current_parsing()