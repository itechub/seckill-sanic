#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import opentracing

from aiomysql import create_pool, DictCursor
from config.utils import jsonify
from config import server

logger = logging.getLogger("sanic")


class BaseConnection(object):
    def __init__(self, pool, conn=None, trace=None):
        self._pool = pool
        self.conn = conn
        self.trace = trace

    @property
    def rowcount(self):
        return self.conn.rowcount

    def before(self, name, query, *args):
        if self.trace:
            with server.jaeger_tracer.start_active_span(name) as scope:
                scope.span.log_kv({"event": "client"})
                scope.span.set_tag("component", "db-execute")
                scope.span.set_tag("db.type", "sql")
                scope.span.set_tag("db.sql", query)
                scope.span.set_tag("args", ",".join([str(a) for a in args]))
                return scope.span

    def finish(self, span):
        if span:
            span.finish()

    async def cursor_execute(self, query: str, *args):
        cursor = await self.conn.cursor(DictCursor)
        res = await cursor.execute(query, *args)
        return cursor

    async def fetchone(self, query, *args):
        span = self.before("fetchone", query, *args)
        cursor = await self.cursor_execute(query)
        res = await cursor.fetchone()
        self.finish(span)
        return res

    async def fetchall(self, query, *args):
        span = self.before("fetchall", query, *args)
        cursor = await self.cursor_execute(query, *args)
        res = await cursor.fetchall()
        self.finish(span)
        return res

    async def insert(self, query, table: str = None, *args):
        span = self.before("insert", query, *args)
        cursor = await self.cursor_execute(query, *args)
        await self.conn.commit()
        res = True
        if table:
            query = f"SELECT * from {table} where id={cursor.lastrowid}"
            res = await self.fetchone(query)
        self.finish(span)
        return res

    # async def execute(self, query: str, *args):
    #    cursor = await self.cursor_execute(query, *args)
    #    return res

    async def executemany(self, command: str, args):
        span = self.before("executemany", command, args)
        res = await self.conn.executemmay(command, args)
        self.finish(span)
        return res

    async def fetchval(self, query, *args, column=0):
        span = self.before("fetchval", query, *args)
        res = await self.conn.fetchval(query, *args, column=column)
        self.finish(span)
        return res

    async def prepare(self, query, *args):
        span = self.before("prepare", query, *args)
        res = await self.conn.prepare(query, *args)
        self.finish(span)
        return res

    async def set_builtin_type_codec(
        self, typename, *args, schema="public", codec_name
    ):
        span = self.before("set_builtin_type_codec", typename, *args)
        await self.conn.set_builtin_type_codec(
            typename, *args, schema=schema, codec_name=codec_name
        )
        self.finish(span)

    async def set_type_codec(
        self, typename, *args, schema="public", encoder, decoder, binary=False
    ):
        span = self.before("set_type_codec", typename, *args)
        await self.conn.set_type_codec(
            typename,
            *args,
            schema=schema,
            encoder=encoder,
            decoder=decoder,
            binary=binary,
        )
        self.finish(span)

    def transaction(
        self, *args, isolation="read_committed", readonly=False, deferrable=False
    ):
        return self.conn.transaction(
            *args, isolation=isolation, readonly=readonly, deferrable=deferrable
        )

    async def release(self):
        await self._pool.release(self.conn)

    async def close(self):
        await self.conn.close()

    async def __aenter__(self):
        self.conn = await self._pool.acquire() if not self.conn else self.conn
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.release()


class TransactionConnection(BaseConnection):
    def __init__(self, pool, span=None, conn=None):
        super(TransactionConnection, self).__init__(pool, span)
        self.conn = conn

    async def __aenter__(self):
        self.conn = await self._pool.acquire() if not self.conn else self.conn
        self.tr = self.transaction()
        await self.tr.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                await self.tr.commit()
            else:
                await self.tr.rollback()
        except:
            pass
        finally:
            await self.release()


class ConnectionPool(object):
    PGHOST = None
    PGUSER = None
    PGPASSWORD = None
    PGPORT = None
    PGDATABASE = None
    pool = None

    def __init__(self, loop=None, trace=False):
        self.conn = None
        self._loop = loop
        self._trace = trace
        self._pool = None

    async def init(self, config, conn=None):
        if conn:
            self.conn = conn
        self._pool = await create_pool(**config, loop=self._loop)
        return self

    def acquire(self, request=None):
        return BaseConnection(self._pool, None, trace=self._trace)

    def transaction(self, request=None):
        return TransactionConnection(
            self._pool, span=request["span"] if request else None, conn=self.conn
        )
