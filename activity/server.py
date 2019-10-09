#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 shady <shady@MrRobot.local>
#

import logging
from sanic import Sanic
from sanic.response import json

from views import seckill_bp
from config import load_config
from config.client import Client
from config.server import app


logger = logging.getLogger("sanic")

# add blueprint
app.blueprint(seckill_bp)


@app.listener("before_server_start")
async def before_srver_start(app, loop):
    app.product_client = Client("seckill-product", app=app)


@app.listener("before_server_stop")
async def before_server_stop(app, loop):
    app.product_client.close()


@app.route("/")
async def index(request):
    return json("activities services")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"], debug=True)
