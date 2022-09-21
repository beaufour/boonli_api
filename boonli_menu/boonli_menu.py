#!/usr/bin/env python
import argparse
import datetime
import logging
import re
from datetime import date
from typing import Dict, Union

import requests
from bs4 import BeautifulSoup
from dateutil.relativedelta import MO, relativedelta
from requests_toolbelt import sessions

ApiData = Dict[str, Union[str, int]]


def create_session(customer_id: str):
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

    # The API key is set in a script tag that just contains the xbat = '...' stance
    soup = BeautifulSoup(login_response.text, features="lxml")
    script_tags = soup.find_all("script")
    api_re = re.compile(r".*xbat.*=.*'(.+)'.*;.*")
    api_token = None
    for script in script_tags:
        match = api_re.match(script.text)
        if match:
            api_token = match.group(1)
            break
    if not api_token:
        raise Exception("Couldn't find API key!")

    logging.debug(f"API Key: {api_token}")

    # TODO: Find out where these magic values come from
    data = {
        "api_token": api_token,
        "pid": "187008",
        "sid": 1,
        "cur_mcid": 6,
    }
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


def get_week(http: requests.Session, api_data: ApiData):
    day = date.today()
    if day.weekday != MO:
        day = day + relativedelta(weekday=MO(-1))
    for i in range(5):
        menu = get_day(http, api_data, day.year, day.month, day.day)
        print(f"Menu for {day.year}.{day.month}.{day.day}: {menu}")
        day = day + datetime.timedelta(days=1)


def main():
    logging.basicConfig()

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--customer_id", type=str, required=True, help="Boonli customer id")
    parser.add_argument("-u", "--username", type=str, required=True, help="Boonli username")
    parser.add_argument("-p", "--password", type=str, required=True, help="Boonli password")
    parser.add_argument("-v", "--verbose", action="store_true", help="Turns on verbose logging")
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    session = create_session(args.customer_id)
    api_data = login(session, args.username, args.password)
    get_week(session, api_data)


if __name__ == "__main__":
    main()
