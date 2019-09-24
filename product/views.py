#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 shady <shady@MrRobot.local>
#

import logging
import ujson
import time
import asyncio

from sanic import Blueprint
from sanic.response import json
from config.server import tracing
from models import *

seckill_bp = Blueprint("seckill", url_prefix="seckill")


@seckill_bp.get("/products", name="list_product")
async def list_product(request):
    async with request.app.db.acquire(request) as cur:
        products = await cur.fetchall(f"SELECT * FROM product;")
    return json(products)


@seckill_bp.get("/products/<id:int>", name="get_product")
@tracing.trace()
async def get_product(request, id):
    async with request.app.db.acquire(request) as cur:
        product = await cur.fetchone(f"SELECT * FROM product WHERE id={id}")
    return json(product)
