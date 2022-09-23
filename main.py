import functions_framework

"""
This is file Cloud Function loads
"""

from flask.wrappers import Request, Response

from boonli_menu.boonli_menu import create_session, get_week, login


@functions_framework.http
def calendar(request: Request) -> Response:
    username = request.args.get("username")
    password = request.args.get("password")
    customer_id = request.args.get("customer_id")
    if not (username and password and customer_id):
        # TODO: be explicit about which one
        raise Exception("Missing a required parameter!")

    session = create_session(customer_id)
    api_data = login(session, username, password)
    menu = get_week(session, api_data)
    headers = {"Content-Type": "text/calendar"}
    return Response(menu, headers=headers)
