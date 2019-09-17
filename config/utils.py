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
            span = request["span"]
            span.set_tag("http.status_code", str(exception.status_code))
            span.set_tag("error.kind", exception.__class__.__name__)
            span.set_tag("error.msg", exception.message)
            return json.dumps(data, status=exception.status_code)
        return super().default(request, exception)


def before_request(request):
    try:
        span_context = opentracing.tracer.extract(
            format=opentracing.Format.HTTP_HEADERS, carrier=request.headers
        )
    except Exception as e:
        span_context = None
    handler = request.app.router.get(request)
    span = opentracing.tracer.start_span(
        operation_name=handler[0].__name__, child_of=span_context
    )
    span.log_kv({"event": "server"})
    span.set_tag("http.url", request.url)
    span.set_tag("http.method", request.method)
    ip = request.ip
    if ip:
        span.set_tag(tags.PEER_HOST_IPV4, "{}:{}".format(ip[0], ip[1]))
    return span


def create_span(
    span_id,
    parent_span_id,
    trace_id,
    span_name,
    start_time,
    duration,
    annotations,
    binary_annotations,
):
    span_dict = {
        "traceId": trace_id,
        "name": span_name,
        "id": span_id,
        "parentId": parent_span_id,
        "timestamp": start_time,
        "duration": duration,
        "annotations": annotations,
        "binaryAnnotations": binary_annotations,
    }
    return span_dict
