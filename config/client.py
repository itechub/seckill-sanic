#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import logging
from aiohttp import ClientSession, hdrs
import opentracing
from config import server

logger = logging.getLogger("sanic")


class Client:
    def __init__(self, name, app=None, url=None, client=None, **kwargs):
        self.name = name
        self._client = client if client else ClientSession(loop=app.loop, **kwargs)
        print("服务启动", app.services)
        self.services = app.services[self.name]
        self._url = url

    def handler_url(self):
        if self._url:
            return
        if self.services:
            print("发起请求", self.services)
            s = random.choice(list(self.services))
            self._url = "http://{}:{}".format(s.service_address, s.service_port)
            print("发起请求 url")
            print(self._url)

    def cli(self, req):
        print("CLI Being called")
        self.handler_url()

        return ClientSessionConn(self._client, url=self._url, trace=True)

    def close(self):
        self._client.close()


class ClientSessionConn:
    _client = None

    def __init__(self, client, url=None, trace=False, **kwargs):
        self._client = client
        self._url = url
        self.trace = trace

    def handler_url(self, url):
        if url.startswith("http"):
            return url
        if self._url:
            return "{}/{}".format(self._url, url)
        return url

    def before(self, method, url):
        if self.trace:
            with server.jaeger_tracer.start_active_span(method) as scope:
                scope.span.log_kv({"event": "client"})
                scope.span.set_tag("http.url", self._url)
                scope.span.set_tag("http.path", url)
                scope.span.set_tag("http.method", method)
                return scope.span
        return None

    def request(self, method, url, **kwargs):
        http_header_carrier = {}
        span = self.before(method, url)
        if span:
            server.jaeger_tracer.inject(
                span.context,
                format=opentracing.Format.HTTP_HEADERS,
                carrier=http_header_carrier,
            )
            res = self._client.request(
                method, self.handler_url(url), headers=http_header_carrier, **kwargs
            )
            span.set_tag("component", "http-client")
            span.finish()
        else:
            res = self._client.request(
                method, self.handler_url(url), headers=http_header_carrier, **kwargs
            )
        return res

    def get(self, url, allow_redirects=True, **kwargs):
        return self.request(hdrs.METH_GET, url, allow_redirects=True, **kwargs)

    def post(self, url, data=None, **kwargs):
        return self.request(hdrs.METH_POST, url, data=data, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.request(hdrs.METH_PUT, url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        return self.request(hdrs.METH_DELETE, url, **kwargs)

    def head(self, url, allow_redirects=False, **kwargs):
        return self.request(
            hdrs.METH_HEAD, url, allow_redirects=allow_redirects, **kwargs
        )

    def options(self, url, allow_redirects=True, **kwargs):
        return self.request(
            hdrs.METH_OPTIONS, url, allow_redirects=allow_redirects, **kwargs
        )

    def close(self):
        self._client.close()
