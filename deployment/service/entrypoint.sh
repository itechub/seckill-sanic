#! /bin/sh
#
# entrypoint.sh
# Copyright (C) 2019 shady <shady@MrRobot.local>
#
# Distributed under terms of the MIT license.
#



#! /bin/sh

set -e

until nc -z -v -w30 $MYSQL_SERVICE_HOST 3306
do
  echo "Waiting for database mysql connection..."
  sleep 5
done >&2

printenv

echo "Migrate Database Model"
cd /service && python3 migrations.py

# Migrate Database Model if not migrated
exec "$@"
