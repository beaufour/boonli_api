"""Misc utility functions used by the API."""
from datetime import timedelta
from typing import List

from icalendar import Calendar, Event

from .api import Menu


def menus_to_ical(menus: List[Menu], domain: str, sequence_num: int = 0) -> bytes:
    """Convert a list of menu entries to iCalendar format.

    `sequence_num` is the icalendar sequence number, see
    https://www.kanzaki.com/docs/ical/sequence.html
    """
    cal = Calendar()
    cal.add("prodid", f"-//Boonli Menu//{domain}//")
    cal.add("version", "2.0")
    cal.add("name", "Boonli Menu")
    cal.add("X-WR-CALNAME", "Boonli Menu")
    cal.add("X-WR-CALDESC", "Boonli Menu")
    for menu in menus:
        if not menu["menu"]:
            continue

        event = Event()
        date_str = f"{menu['day'].year}{menu['day'].month:02}{menu['day'].day:02}"
        event["uid"] = date_str
        if sequence_num:
            event["sequence"] = str(sequence_num)
        # TODO: It would be more conformant to have;DATE=VALUE...
        event["dtstart"] = date_str
        event["summary"] = menu["menu"]
        day = menu["day"] + timedelta(days=1)
        event["dtend"] = f"{day.year}{day.month:02}{day.day:02}"
        event["organizer"] = f"donotreply@{domain}"
        cal.add_component(event)

    return cal.to_ical()
