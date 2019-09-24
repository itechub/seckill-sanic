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
from config.tracer import init_tracer
from sanic_opentracing import SanicTracing


config = load_config()
appid = config.get("APP_ID", __name__)
trace_all = config.get("TRACE_ALL", False)
jaeger_host = config.get("JAEGER_HOST", "localhost")

app = Sanic(appid, error_handler=CustomHandler())
app.blueprint(swagger_blueprint)
app.config = config
jaeger_tracer = init_tracer(appid, jaeger_host)
tracing = SanicTracing(tracer=jaeger_tracer, trace_all_requests=trace_all, app=app)


@app.listener("before_server_start")
async def before_server_start(app, loop):
    config = app.config["DB_CONFIG"]
    # Config for Mysql Connection
    config["db"] = config["database"]
    del config["database"]
    app.db = await ConnectionPool(loop=loop, trace=True).init(app.config["DB_CONFIG"])


@app.exception(RequestTimeout)
def timeout(request, exception):
    return json({"message": "Request Timeout"}, 408)


@app.exception(NotFound)
def notfound(request, exception):
    return json({"message": "Requested URL {} not found".format(request.url)}, 404)
