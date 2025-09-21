from typing import List
from tools.tool import BaseTool, Params
from services.service import get_calendar_service

class DeleteEvent(BaseTool):
    @property
    def name(self) -> str:
        return "DeleteEvent"

    @property
    def description(self) -> str:
        return "Deletes an event from Google Calendar using its event ID."

    @property
    def parameters(self) -> List[Params]:
        return [
            Params(
                name="event_id",
                type="string",
                description="The ID of the event to delete"
            )
        ]

    def execute(self, event_id: str) -> str:
        try:
            service = get_calendar_service()
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return f"Event {event_id} deleted."
        except Exception as e:
            return f"Error: {str(e)}"
