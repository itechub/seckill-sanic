#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import asyncio
import opentracing

from sanic.handlers import ErrorHandler
from opentracing.ext import tags
from .exceptions import CustomException, NotFound

logger = logging.getLogger("sanic")
_log = logging.getLogger("zipkin")

PAGE_COUNT = 20


def jsonify(records):
    """
    Parse asyncpg record response into JSON format
    """
    if not records:
        raise NotFound()
        return []
    return [dict(r.items()) for r in records]


async def async_request(calls):
    results = await asyncio.gather(*[call[2] for call in calls])
    for index, obj in enumerate(results):
        call = calls[index]
        call[0][call[1]] = results[index]


async def async_execute(*calls):
    results = await asyncio.gather(*calls)
    return tuple(results)


def id_to_hex(id):
    if id is None:
        return None
    return "{0:x}".format(id)


class CustomHandler(ErrorHandler):
    def default(self, request, exception):
        if isinstance(exception, CustomException):
            data = {"message": exception.message, "code": exception.code}
            if exception.error:
                data.update({"error": exception.error})
            return json.dumps(data, status=exception.status_code)
        return super().default(request, exception)
