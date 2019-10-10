#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 shady <shady@MrRobot.local>
#
import datetime
from peewee import MySQLDatabase
from peewee import Model, BooleanField, IntegerField, DateTimeField, PrimaryKeyField
from config import load_config

config = load_config()
db = MySQLDatabase(**config["DB_CONFIG"])


class Order(Model):
    uuid = IntegerField()
    activity = IntegerField()
    payment = BooleanField(default=False)
    created = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = "order"
        database = db
