#!/usr/bin/env python
import argparse
import datetime
import logging
from datetime import date
from typing import Dict, Union

import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import MO, relativedelta
from icalendar import Calendar, Event
from requests_toolbelt import sessions

ApiData = Dict[str, Union[str, int]]


def create_session(customer_id: str) -> requests.Session:
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


def login(http: requests.Session, username: str, password: str) -> ApiData:
    url = "login"
    logging.debug(f"\n########## Login GET {url}")
    resp = http.get(url)
    soup = BeautifulSoup(resp.text, features="lxml")
    token_tag = soup.find(attrs={"name": "csrftk"})
    if not token_tag:
        raise Exception("Could not find token tag!")

    token = token_tag.get("value")  # type: ignore
    logging.debug(f"Token: {token}")
    logging.debug(f"Cookies: {http.cookies}")

    logging.debug(f"\n########## Login POST {url}")
    data = {
        "username": username,
        "password": password,
        "csrftk": token,
    }
    login_response = http.post(url, data=data)
    logging.debug(f"Login post: {login_response}")
    logging.debug(f"Headers: {login_response.request.headers}")
    logging.debug(f"Cookies: {http.cookies}")

    soup = BeautifulSoup(login_response.text, features="lxml")
    api_token_tag = soup.find("input", attrs={"id": "lxbat"})
    if not api_token_tag:
        raise Exception("Couldn't find value for API token!")
    api_token = str(api_token_tag.get("value"))  # type: ignore
    sid_tag = soup.find("input", attrs={"name": "sid"})
    if not sid_tag:
        raise Exception("Couldn't find value for SID")
    sid = int(sid_tag.get("value"))  # type: ignore
    pid_tag = soup.find("input", attrs={"name": "pid"})
    if not pid_tag:
        raise Exception("Couldn't find value for PID")
    pid = int(pid_tag.get("value"))  # type: ignore
    cur_mcid_tag = soup.find("a", attrs={"class": "mcycle_button"})
    if not cur_mcid_tag:
        raise Exception("Couldn't find value for MCID")
    cur_mcid = int(cur_mcid_tag.get("id"))  # type: ignore
    logging.debug(f"Selecting for {cur_mcid_tag.text}")

    data = {
        "api_token": api_token,
        "pid": pid,
        "sid": sid,
        "cur_mcid": cur_mcid,
    }
    logging.debug(f"API Data: {data}")
    return data


def get_day(http: requests.Session, api_data: ApiData, year: int, month: int, day: int) -> str:
    api_data.update(
        {
            "cy": year,
            "cm": month,
            "cday": day,
        }
    )
    url = "api/cal/getDay"
    api_response = http.post(url, data=api_data)
    api_json = api_response.json()
    alert_msg = api_json.get("alert_msg")
    if alert_msg:
        logging.info(f"Got alert message for {year}-{month}-{day}: {alert_msg}")

    soup = BeautifulSoup(api_json["body"], features="lxml")
    menu_tag = soup.find(attrs={"class": "menu-name"})
    if not menu_tag:
        logging.debug(f"Missing menu tag in API Response: {api_json}")
        return alert_msg or ""
    # This takes the second child, to skip the item_preface element
    # <span class=\"menu-name\"><span class=\"item_preface\">02-Pasta<\/span>
    # Macaroni and Cheese w\/ Sliced Cucumbers (on the side)<\/span>
    menu = menu_tag.contents[1].text.strip()  # type: ignore
    return menu


def get_week(http: requests.Session, api_data: ApiData) -> str:
    day = date.today()
    if day.weekday != MO:
        day = day + relativedelta(weekday=MO(-1))

    cal = Calendar()
    cal.add("prodid", "-//Boonli Menu//beaufour.dk//")
    cal.add("version", "2.0")
    cal.add("name", "Boonli Menu")
    cal.add("X-WR-CALNAME", "Boonli Menu")
    cal.add("X-WR-CALDESC", "Boonli Menu")
    for i in range(5):
        menu = get_day(http, api_data, day.year, day.month, day.day)
        print(f"Menu for {day.year}.{day.month}.{day.day}: {menu}")
        event = Event()
        date_str = f"{day.year}{day.month:02}{day.day:02}"
        event["uid"] = date_str
        # TODO: should do the ;DATE=VALUE thing here...
        event["dtstart"] = date_str
        event["summary"] = menu
        day = day + datetime.timedelta(days=1)
        event["dtend"] = f"{day.year}{day.month:02}{day.day:02}"
        event["organizer"] = "donotreply@beaufour.dk"
        cal.add_component(event)
    return str(cal.to_ical())


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

    session = create_session(args.customer_id)
    api_data = login(session, args.username, args.password)
    print(get_week(session, api_data))


if __name__ == "__main__":
    main()
