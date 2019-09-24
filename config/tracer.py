#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 shady <shady@MrRobot.local>
#

"""
Jaeger tracer init
"""
import os
import logging
from jaeger_client import Config


def init_tracer(service, jaeger_host):
    logging.getLogger("").handlers = []
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)

    config = Config(
        config={
            "sampler": {"type": "const", "param": 1},
            "logging": True,
            "local_agent": {"reporting_host": jaeger_host},
        },
        service_name=service,
    )
    return config.initialize_tracer()
