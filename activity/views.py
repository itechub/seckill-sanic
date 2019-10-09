#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 shady <shady@MrRobot.local>
#

import logging
import datetime
import time
import asyncio

from sanic import Blueprint
from sanic.response import json
from config.server import tracing
from models import *

seckill_bp = Blueprint("activity", url_prefix="activities")


async def get_product_by_id(request, id):
    cli = request.app.product_client.cli(request)
    async with cli.get(f"products/{id}") as res:
        return await res.json()


@seckill_bp.post("/", name="create_activity")
async def create_activity(request):
    data = request["data"]
    created_time = datetime.datetime.now()
    async with request.app.db.acquire(request) as cur:
        sql_command = "INSERT INTO activity(name, product, start_time, end_time, created) VALUES(%s, %s, %s,%s, %s)"
        activity = await cur.insert(
            sql_command,
            "activity",
            (
                data["name"],
                data["product"],
                data["start_time"],
                data["end_time"],
                created_time,
            ),
        )
    return json(activity)


@seckill_bp.get("/", name="list_activity")
async def list_activity(request):
    async with request.app.db.acquire(request) as cur:
        activities = await cur.fetchall(f"SELECT * FROM activity;")
    return json(activities)


@seckill_bp.get("/<id:int>", name="get_activity")
async def get_activity(request, id):
    async with request.app.db.acquire(request) as cur:
        activity = await cur.fetchone(f"SELECT * FROM activity WHERE id={id}")
    activity["product"] = await get_product_by_id(request, activity["product"])
    return json(activity)
