"""
Init for fileMangSys.
Installs PyMySQL as MySQLdb driver for MySQL connectivity and ensures compatibility with MariaDB 10.4.
"""
import pymysql

pymysql.install_as_MySQLdb()

# Configure Django MySQL DatabaseWrapper & DatabaseFeatures
from django.db.backends.mysql.base import DatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures

# 1. Skip minimum version check for MariaDB 10.4
DatabaseWrapper.check_database_version_supported = lambda self: None

# 2. MariaDB < 10.5 does not support INSERT ... RETURNING syntax
DatabaseFeatures.can_return_columns_from_insert = property(lambda self: False)
DatabaseFeatures.can_return_rows_from_bulk_insert = property(lambda self: False)
