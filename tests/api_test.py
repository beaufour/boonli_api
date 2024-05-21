"""Tests for the Boonli API."""

import json
import pathlib
from typing import Any

import pytest

from boonli_api.api import (
    APIError,
    BoonliAPI,
    LoginError,
    ParseError,
    _extract_api_data,
    _extract_csrf_token,
    _extract_menu,
)

FIXTURE_DIR = pathlib.Path(__file__).parent.resolve() / "fixtures"


def load_fixture(path: str) -> str:
    """Helper function to load test input file."""
    file_ = open(FIXTURE_DIR / path, "r", encoding="utf-8")
    return file_.read()


def load_json_fixture(path: str) -> Any:
    """Helper function to load test input file in JSON format."""
    return json.loads(load_fixture(path))


def test_extract_csrf_token() -> None:
    """Tests that we correctly get the CSRF token."""
    assert (
        _extract_csrf_token(load_fixture("boonli_login_1.html"))
        == "245EFF7C-BC24-463D-B6B1-CD34B1002DC5"
    )
    with pytest.raises(Exception):
        # This is missing the token
        _extract_csrf_token(load_fixture("boonli_login_2.html"))


def test_extract_api_data() -> None:
    """Tests that we correctly get critical API data from the html."""
    assert _extract_api_data(load_fixture("boonli_home_1.html")) == {
        "api_token": "7C8C2555-FD5F-4AA1-BD4F-43C48B44E425",
        "pid": 100001,
        "sid": 1,
        "cur_mcid": 6,
    }

    with pytest.raises(ParseError):
        # This is missing the mcid
        _extract_api_data(load_fixture("boonli_home_2.html"))

    with pytest.raises(LoginError):
        _extract_api_data(load_fixture("boonli_login_invalid_username.html"))


def test_extract_menu() -> None:
    """Tests that we correctly get the menu from the "API"."""
    assert _extract_menu(load_json_fixture("day_no_menu.json")) == ""
    assert _extract_menu(load_json_fixture("day_no_menu_alert.json")) == "School is closed!"
    assert (
        _extract_menu(load_json_fixture("day_menu_1.json"))
        == "Macaroni and Cheese w/ Sliced Cucumbers (on the side)"
    )

    with pytest.raises(LoginError):
        _extract_menu(load_json_fixture("day_unauth.json"))

    with pytest.raises(APIError):
        _extract_menu(load_json_fixture("day_server_error.json"))


def test_invalid_customer_id() -> None:
    """Tests that we correctly handle invalid Boonli Customer IDs (ie urls
    really)."""
    api = BoonliAPI()
    with pytest.raises(LoginError):
        api.login("Iamconvincedthisdoesnotexist", "username", "password")


def test_multiple_mctypes() -> None:
    """Tests that we correctly handle multiple mc ids."""
    assert _extract_api_data(load_fixture("boonli_home_3.html")) == {
        "api_token": "8464B60E-2294-4248-9406-4AF01A676444",
        "pid": 909456,
        "sid": 1,
        "cur_mcid": 12,
    }
