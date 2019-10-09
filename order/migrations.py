import sys
from config import load_config
from peewee import MySQLDatabase
from models import Order


config = load_config()

db = MySQLDatabase(**config["DB_CONFIG"])


try:
    db.create_tables([Order])
except Exception as e:
    pass
