#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 shady <shady@MrRobot.local>
#

import logging
import time
import asyncio

from sanic import Blueprint
from sanic.response import json
from config.server import tracing
from models import *

seckill_bp = Blueprint("order", url_prefix="orders")


@seckill_bp.get("/", name="list_order")
async def list_order(request):
    async with request.app.db.acquire(request) as cur:
        orders = await cur.fetchall(f"SELECT * FROM `order`;")
    return json(orders)


@seckill_bp.get("/<id:int>", name="get_order")
@tracing.trace()
async def get_order(request, id):
    async with request.app.db.acquire(request) as cur:
        order = await cur.fetchone(f"SELECT * FROM `order` WHERE id={id}")
    return json(order)
