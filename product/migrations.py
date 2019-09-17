import sys
from util import load_config
from peewee import MySQLDatabase
from models import Product, Activity, Order


config = load_config()

db = MySQLDatabase(**config["DB_CONFIG"])


try:
    db.create_tables([Product, Activity, Order])
except Exception as e:
    pass
