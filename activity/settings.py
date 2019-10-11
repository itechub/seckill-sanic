import os

"""
Basic config
"""
APP_ID = "seckill-activity"

HOST = os.environ.get("SERVER_HOST", None)
PORT = int(os.environ.get("SERVER_PORT", 8504))

TRACE_ALL = os.environ.get("TRACE_ALL", False)
JAEGER_HOST = os.environ.get("JAEGER_HOST", "localhost")

DB_CONFIG = {
    "host": os.environ.get("MYSQL_SERVICE_HOST", "localhost"),
    "user": os.environ.get("MYSQL_SERVICE_USER", "mysql"),
    "password": os.environ.get("MYSQL_SERVICE_PASSWORD", None),
    "port": int(os.environ.get("MYSQL_SERVICE_PORT", 3306)),
    "database": os.environ.get("MYSQL_SERVICE_DB_NAME", "seckill_activity"),
}

SWAGGER = {
    "version": "1.0.0",
    "title": "SECKILL ACTIVITY API",
    "description": "SECKILL ACTIVITY SERVICE  API BASED ON SANIC",
    "terms_of_service": "Use with caution!",
    "termsOfService": ["application/json"],
    "contact_email": "shady@camfire.com",
}

ACCESS_CONTROL_ALLOW_ORIGIN = os.environ.get("ACCESS_CONTROL_ALLOW_ORIGIN", "")
ACCESS_CONTROL_ALLOW_HEADERS = os.environ.get("ACCESS_CONTROL_ALLOW_HEADERS", "")
ACCESS_CONTROL_ALLOW_METHODS = os.environ.get("ACCESS_CONTROL_ALLOW_METHODS", "")

CONSUL_AGENT_HOST = os.environ.get("CONSUL_AGENT_HOST", "127.0.0.1")
CONSUL_AGENT_PORT = os.environ.get("CONSUL_AGENT_PORT", 8500)
