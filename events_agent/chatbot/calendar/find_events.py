from typing import List
from tools.tool import BaseTool, Params
from services.service import get_calendar_service
from datetime import datetime, timedelta

class FindEvent(BaseTool):
    @property
    def name(self) -> str:
        return "FindEvent"

    @property
    def description(self) -> str:
        return "Finds upcoming Google Calendar events containing a keyword."

    @property
    def parameters(self) -> List[Params]:
        return [
            Params(
                name="keyword",
                type="string",
                description="Keyword to search for in event summaries or descriptions"
            )
        ]

    def execute(self, keyword: str) -> str:
        try:
            service = get_calendar_service()
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=20,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            matching = []
            for event in events:
                summary = event.get('summary', '')
                description = event.get('description', '')
                if keyword.lower() in summary.lower() or keyword.lower() in description.lower():
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    matching.append(f"- {summary} at {start} (ID: {event['id']})")

            if not matching:
                return f"No upcoming events found with keyword '{keyword}'."
            return f"Matching events:\n" + "\n".join(matching)

        except Exception as e:
            return f"Error: {str(e)}"
