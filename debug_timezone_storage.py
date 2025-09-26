#!/usr/bin/env python3
"""
Test to understand the timezone storage issue
"""

import sys
import os
from datetime import datetime
import pytz

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from events_agent.infra.date_parsing import parse_natural_range
from events_agent.infra.settings import settings

def test_timezone_storage_issue():
    """Test the timezone storage issue"""
    print("🔍 ANALYZING TIMEZONE STORAGE ISSUE")
    print("=" * 50)
    
    # Parse "3PM September 27" (tomorrow)
    test_input = "3PM September 27"
    print(f"Input: '{test_input}'")
    
    try:
        start_dt, end_dt = parse_natural_range(test_input, settings.default_tz)
        
        print(f"Parsed datetime: {start_dt}")
        print(f"Timezone: {start_dt.tzinfo}")
        print(f"ISO format: {start_dt.isoformat()}")
        
        # This is what goes to Google Calendar
        google_event_body = {
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "Australia/Melbourne",
            }
        }
        
        print(f"\nGoogle Calendar event body:")
        print(f"  dateTime: {google_event_body['start']['dateTime']}")
        print(f"  timeZone: {google_event_body['start']['timeZone']}")
        
        # The issue: Google Calendar might interpret this differently
        print(f"\n🔍 POTENTIAL ISSUE:")
        print(f"If Google Calendar sees: {start_dt.isoformat()}")
        print(f"With timezone: Australia/Melbourne")
        print(f"It might double-convert the timezone!")
        
        # Better approach: Strip timezone info and let Google handle it
        start_dt_naive = start_dt.replace(tzinfo=None)
        print(f"\nBETTER APPROACH:")
        print(f"Send naive datetime: {start_dt_naive.isoformat()}")
        print(f"With explicit timezone: Australia/Melbourne")
        print(f"Let Google Calendar handle the timezone conversion")
        
        # Convert to UTC explicitly (what Google actually stores)
        start_utc = start_dt.astimezone(pytz.UTC)
        print(f"\nWhat Google Calendar actually stores:")
        print(f"UTC time: {start_utc.isoformat()}")
        
        # Show the 10-hour difference
        hour_diff = start_dt.hour - start_utc.hour
        if hour_diff < 0:
            hour_diff += 24
        print(f"Time difference: {hour_diff} hours")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_timezone_storage_issue()