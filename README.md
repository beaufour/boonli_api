# Boonli API

[![Build Status](https://app.travis-ci.com/beaufour/boonli_api.svg?branch=main)](https://app.travis-ci.com/beaufour/boonli_api) [![Coverage Status](https://coveralls.io/repos/github/beaufour/boonli_api/badge.svg?branch=main)](https://coveralls.io/github/beaufour/boonli_api?branch=main) [![PyPI version](https://badge.fury.io/py/boonli_api.svg)](https://badge.fury.io/py/boonli_api)

This API allows you to retrieve the menus that were chosen on [Boonli](https://boonli.com).

## Usage

To get the menu information run:

    > boonli_api/api.py -c <customer_id> -u <username> -p <password>

Where `customer_id` is the first part of the domain name where you login, like `my_school` in `https://myschool.boonli.com`.

To enable a lot of debug logging you can add `-v`.

## Web API

I have also created an API that can be deployed on Google Cloud Function that returns the menus as an iCalendar here: <https://github.com/beaufour/boonli_calendar>

## Notes

Boonli does not have an official API, so I reverse engineered it. It involves parsing two web pages which is always fragile. So it will probably break at some point.
