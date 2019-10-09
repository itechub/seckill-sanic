#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 shady <shady@MrRobot.local>
#
import datetime
from peewee import MySQLDatabase
from peewee import Model, CharField, IntegerField, DateTimeField, PrimaryKeyField
from config import load_config

config = load_config()
db = MySQLDatabase(**config["DB_CONFIG"])


class Activity(Model):
    id = PrimaryKeyField()
    name = CharField(max_length=250)
    product = IntegerField()
    start_time = DateTimeField()
    end_time = DateTimeField()
    created = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = "activity"
        database = db
