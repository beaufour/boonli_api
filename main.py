"""
This is file Cloud Function loads
"""

from datetime import date, timedelta

import functions_framework
from dateutil.relativedelta import MO, relativedelta
from flask.wrappers import Request, Response

from boonli_api.api import BoonliAPI
from boonli_api.utils import menus_to_ical


@functions_framework.http
def calendar(request: Request) -> Response:
    """
    Returns three weeks worth of menus in icalendar format (last, current, and next week)
    """
    username = request.args.get("username")
    password = request.args.get("password")
    customer_id = request.args.get("customer_id")
    if not (username and password and customer_id):
        # TODO: be explicit about which one
        raise Exception("Missing a required parameter!")

    api = BoonliAPI()
    api.login(customer_id, username, password)

    day = date.today()
    if day.weekday != MO:
        day = day + relativedelta(weekday=MO(-1))
    day -= timedelta(days=-7)

    # Get last week, this, and next (ie 21 days)
    menus = api.get_range(day, 21)
    ical = menus_to_ical(menus, "beaufour.dk")
    headers = {"Content-Type": "text/calendar"}
    return Response(ical, headers=headers)
