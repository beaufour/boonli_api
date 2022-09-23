import functions_framework

"""
This is file Cloud Function loads
"""

from flask.wrappers import Request, Response

from boonli_api.api import BoonliAPI


@functions_framework.http
def calendar(request: Request) -> Response:
    username = request.args.get("username")
    password = request.args.get("password")
    customer_id = request.args.get("customer_id")
    if not (username and password and customer_id):
        # TODO: be explicit about which one
        raise Exception("Missing a required parameter!")

    api = BoonliAPI()
    api.login(customer_id, username, password)
    menu = api.get_week()
    headers = {"Content-Type": "text/calendar"}
    return Response(menu, headers=headers)
