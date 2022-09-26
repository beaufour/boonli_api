"""This is file Cloud Function loads."""

from base64 import b64decode
from datetime import date, timedelta
from urllib.parse import parse_qs

import functions_framework
from dateutil.relativedelta import MO, relativedelta
from flask.wrappers import Request, Response

from boonli_api.api import BoonliAPI
from boonli_api.utils import menus_to_ical


@functions_framework.http
def calendar(request: Request) -> Response:
    """Returns three weeks worth of menus in icalendar format (last, current,
    and next week)

    The function takes `username`, `password` and `customer_id` as query params.

    You can also pass them in through `id` with the query params as a base64
    encoded UTF-8 string. This is terrible "security" but at least people don't
    see your password directly if they look at your calendar list? Or see it in
    a query log.

    To create the id in Python:
    > from base64 import b64encode; b64encode(bytes('username=...&password=...&customer_id=...', 'UTF-8'))
    """
    id = request.args.get("id")
    if id:
        url_string = b64decode(id).decode("utf-8")
        args_list = parse_qs(url_string)
        args = {}
        for arg in args_list.keys():
            args[arg] = args_list[arg][0]
    else:
        args = request.args

    username = args.get("username")
    password = args.get("password")
    customer_id = args.get("customer_id")

    if not (username and password and customer_id):
        # TODO: be explicit about which one
        raise Exception("Missing a required parameter!")

    api = BoonliAPI()
    api.login(customer_id, username, password)

    day = date.today()
    sequence_num = day.toordinal()

    # Start listening menus from a Monday. List menus from last week and show
    # 21 days from then
    if day.weekday() != MO:
        day = day + relativedelta(weekday=MO(-1))
    day -= timedelta(days=7)
    menus = api.get_range(day, 21)

    # we set the sequence number to the current day as a hack, because without
    # storing anything we don't know if anything has changed. that way it
    # monotonically increases at least.
    ical = menus_to_ical(menus, "beaufour.dk", sequence_num=sequence_num)
    headers = {"Content-Type": "text/calendar"}
    return Response(ical, headers=headers)
