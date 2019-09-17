#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import datetime
import yaml
import os
import opentracing

from collections import defaultdict

from sanic import Sanic, config
from sanic.response import json, text, HTTPResponse
from sanic.exceptions import RequestTimeout, NotFound
from sanic_openapi import swagger_blueprint


from config import load_config
from config.db import ConnectionPool
from config.utils import CustomHandler
from config.exceptions import NotFound

from config.utils import before_request

config = load_config()
appid = config.get("APP_ID", __name__)
app = Sanic(appid, error_handler=CustomHandler())
app.config = config
app.blueprint(swagger_blueprint)


@app.listener("before_server_start")
async def before_server_start(app, loop):
    config = app.config["DB_CONFIG"]
    # Config for Mysql Connection
    config["db"] = config["database"]
    del config["database"]
    app.db = await ConnectionPool(loop=loop).init(app.config["DB_CONFIG"])


@app.middleware("request")
async def cros(request):
    config = request.app.config
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": config["ACCESS_CONTROL_ALLOW_ORIGIN"],
            "Access-Control-Allow-Headers": config["ACCESS_CONTROL_ALLOW_HEADERS"],
            "Access-Control-Allow-Methods": config["ACCESS_CONTROL_ALLOW_METHODS"],
        }
        return json({"code": 0}, headers=headers)
    if request.method == "POST" or request.method == "PUT":
        request["data"] = request.json
    span = before_request(request)
    request["span"] = span


@app.middleware("response")
async def cors_res(request, response):
    config = request.app.config
    span = request["span"] if "span" in request else None
    if response is None:
        return response
    result = {"code": 0}
    if not isinstance(response, HTTPResponse):
        if isinstance(response, tuple) and len(response) == 2:
            result.update({"data": response[0], "pagination": response[1]})
        else:
            result.update({"data": response})
        response = json(result)
        if span:
            span.set_tag("http.status_code", "200")
    if span:
        span.set_tag("component", request.app.name)
        span.finish()
    response.headers["Access-Control-Allow-Origin"] = config[
        "ACCESS_CONTROL_ALLOW_ORIGIN"
    ]
    response.headers["Access-Control-Allow-Headers"] = config[
        "ACCESS_CONTROL_ALLOW_HEADERS"
    ]
    response.headers["Access-Control-Allow-Methods"] = config[
        "ACCESS_CONTROL_ALLOW_METHODS"
    ]
    return response


@app.exception(RequestTimeout)
def timeout(request, exception):
    return json({"message": "Request Timeout"}, 408)


@app.exception(NotFound)
def notfound(request, exception):
    return json({"message": "Requested URL {} not found".format(request.url)}, 404)
