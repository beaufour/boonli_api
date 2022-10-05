#!/usr/bin/env python
import argparse
import logging
import sys
from datetime import date, timedelta
from typing import Any, Dict, List, Union

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import MO, relativedelta
from requests_toolbelt import sessions

ApiData = Dict[str, Union[str, int]]


class ParseError(Exception):
    """If we cannot parse the returned data."""

    pass


class LoginError(Exception):
    """If we cannot login to the Boonli website."""

    pass


class APIError(Exception):
    """If the Boonli website returns and error."""

    pass


class Menu(TypedDict):
    "The menu for a given date"
    menu: Union[str, None]
    day: date


def _create_session(customer_id: str) -> requests.Session:
    """Creates a requests session with the base API url, headers, etc."""
    base_url = f"https://{customer_id}.boonli.com/"
    http = sessions.BaseUrlSession(base_url=base_url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:86.0) Gecko/20100101 Firefox/86.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": base_url,
        "Connection": "keep-alive",
    }
    http.headers.update(headers)
    return http


def _extract_csrf_token(text: str) -> str:
    soup = BeautifulSoup(text, features="lxml")
    token_tag = soup.find(attrs={"name": "csrftk"})
    if not token_tag:
        raise ParseError("Could not find token tag!")

    token = token_tag.get("value")  # type: ignore
    return str(token)


def _extract_api_data(text: str) -> ApiData:
    if "Invalid username/password" in text:
        # Man, this is an ugly way to detect that
        raise LoginError("Wrong username/password")

    soup = BeautifulSoup(text, features="lxml")
    api_token_tag = soup.find("input", attrs={"id": "lxbat"})
    if not api_token_tag:
        raise ParseError("Couldn't find value for API token!")
    api_token = str(api_token_tag.get("value"))  # type: ignore
    sid_tag = soup.find("input", attrs={"name": "sid"})
    if not sid_tag:
        raise ParseError("Couldn't find value for SID")
    sid = int(sid_tag.get("value"))  # type: ignore
    pid_tag = soup.find("input", attrs={"name": "pid"})
    if not pid_tag:
        raise ParseError("Couldn't find value for PID")
    pid = int(pid_tag.get("value"))  # type: ignore
    cur_mcid_tag = soup.find("a", attrs={"class": "mcycle_button"})
    if not cur_mcid_tag:
        raise ParseError("Couldn't find value for MCID")
    cur_mcid = int(cur_mcid_tag.get("id"))  # type: ignore
    logging.debug(f"Selecting for {cur_mcid_tag.text}")

    data: ApiData = {
        "api_token": api_token,
        "pid": pid,
        "sid": sid,
        "cur_mcid": cur_mcid,
    }
    return data


def _extract_menu(json: Any) -> str:
    alert_msg = json.get("alert_msg")
    if alert_msg:
        logging.info(f"Got alert message: {alert_msg}")
    error = json.get("error")
    if error:
        if error == "unauthenticated":
            raise LoginError("Unauthenticated")

        raise APIError(f"Got an error from the API: {error}")

    soup = BeautifulSoup(json["body"], features="lxml")
    menu_tag = soup.find(attrs={"class": "menu-name"})
    if not menu_tag:
        logging.debug(f"Missing menu tag in API Response: {json}")
        return alert_msg or ""
    # This takes the second child, to skip the item_preface element
    # <span class=\"menu-name\"><span class=\"item_preface\">02-Pasta<\/span>
    # Macaroni and Cheese w\/ Sliced Cucumbers (on the side)<\/span>
    return menu_tag.contents[1].text.strip()  # type: ignore


class BoonliAPI:
    """The main API.

    Call :func:`~boonli.api.BoonliAPI.login` first, before using any
    other methods.
    """

    _session = None
    _api_data = None

    def login(self, customer_id: str, username: str, password: str) -> None:
        """Logs into the Boonli API and retrieves the API parameters used for
        doing API calls."""
        if self._session or self._api_data:
            logging.warn("Already logged in")
            return

        self._session = _create_session(customer_id)

        url = "login"
        logging.debug(f"\n########## Login GET {url}")
        resp = self._session.get(url)
        token = _extract_csrf_token(resp.text)
        logging.debug(f"Token: {token}")
        logging.debug(f"Cookies: {self._session.cookies}")

        logging.debug(f"\n########## Login POST {url}")
        data = {
            "username": username,
            "password": password,
            "csrftk": token,
        }
        login_response = self._session.post(url, data=data)
        logging.debug(f"Login post: {login_response}")
        logging.debug(f"Headers: {login_response.request.headers}")
        logging.debug(f"Cookies: {self._session.cookies}")

        self._api_data = _extract_api_data(login_response.text)
        logging.debug(f"API Data: {self._api_data}")

    def get_day(self, day: date) -> str:
        """Returns the menu for the given day."""
        if not self._api_data or not self._session:
            raise Exception("Not logged in")

        data = self._api_data.copy()
        data.update(
            {
                "cy": day.year,
                "cm": day.month,
                "cday": day.day,
            }
        )
        url = "api/cal/getDay"
        api_response = self._session.post(url, data=data)
        api_json = api_response.json()
        menu = _extract_menu(api_json)
        return menu

    def get_range(self, start: date, count: int) -> List[Menu]:
        """Returns the menu from a `start` date and `count` days forward."""
        ret = []
        for i in range(count):
            menu = self.get_day(start)
            ret.append(Menu(menu=menu, day=start))
            start += timedelta(days=1)
        return ret


def main() -> None:
    logging.basicConfig()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--customer_id",
        type=str,
        required=True,
        help="Boonli customer id, ie the first part of the domain name you log in on",
    )
    parser.add_argument("-u", "--username", type=str, required=True, help="Boonli username")
    parser.add_argument("-p", "--password", type=str, required=True, help="Boonli password")
    parser.add_argument("-v", "--verbose", action="store_true", help="Turns on verbose logging")
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    api = BoonliAPI()
    api.login(args.customer_id, args.username, args.password)
    day = date.today()
    if day.weekday() != MO:
        day = day + relativedelta(weekday=MO(-1))
    print(api.get_range(day, 7))


if __name__ == "__main__":
    main()
