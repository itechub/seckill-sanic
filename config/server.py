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
from config.service import ServiceManager, service_watcher
from sanic_opentracing import SanicTracing


config = load_config()
appid = config.get("APP_ID", __name__)
trace_all = config.get("TRACE_ALL", False)
jaeger_host = config.get("JAEGER_HOST", "localhost")

app = Sanic(appid, error_handler=CustomHandler())
app.blueprint(swagger_blueprint)
app.config = config
jaeger_tracer = init_tracer(appid, jaeger_host)
tracing = SanicTracing(
    tracer=jaeger_tracer,
    trace_all_requests=trace_all,
    app=app,
    exceptions=[RuntimeError],
)


@app.listener("before_server_start")
async def before_server_start(app, loop):
    config = app.config["DB_CONFIG"]
    # Config for Mysql Connection
    config["db"] = config["database"]
    del config["database"]
    app.add_task(service_watcher(app, loop))
    app.db = await ConnectionPool(loop=loop, trace=True).init(app.config["DB_CONFIG"])


@app.listener("after_server_start")
async def after_server_start(app, loop):
    service = ServiceManager(app.name, loop=loop, host=app.config["CONSUL_AGENT_HOST"])
    await service.register_service(port=app.config["PORT"])
    app.service = service


@app.listener("before_server_stop")
async def before_server_stop(app, loop):
    await app.service.deregister()


@app.middleware("request")
async def preempt_cros(request):
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


@app.middleware("response")
async def cors_res(request, response):
    config = request.app.config
    response.headers["Access-Control-Allow-Origin"] = config[
        "ACCESS_CONTROL_ALLOW_ORIGIN"
    ]
    response.headers["Access-Control-Allow-Headers"] = config[
        "ACCESS_CONTROL_ALLOW_HEADERS"
    ]
    response.headers["Access-Control-Allow-Methods"] = config[
        "ACCESS_CONTROL_ALLOW_METHODS"
    ]


# Common envelop for response
@app.middleware("response")
async def wrap_response(request, response):
    if response is None:
        return response
    result = {"code": 0}
    if not isinstance(response, HTTPResponse):
        if isinstance(response, tuple) and len(response) == 2:
            result.update({"data": response[0], "pagination": response[1]})
        else:
            result.update({"data": response})
        response = json(result)


@app.exception(RequestTimeout)
def timeout(request, exception):
    return json({"msg": "Request Timeout"}, 408)


@app.exception(NotFound)
def notfound(request, exception):
    return json({"msg": "Requested URL {} not found".format(request.url)}, 404)
