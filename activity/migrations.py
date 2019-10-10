import sys
from config import load_config
from peewee import MySQLDatabase
from models import Activity


config = load_config()

db = MySQLDatabase(**config["DB_CONFIG"])


try:
    db.create_tables([Activity])
except Exception as e:
    pass
