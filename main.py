import functions_framework

"""
This is file Cloud Function loads
"""


@functions_framework.http
def calendar(request):
    return "Hello world!"
