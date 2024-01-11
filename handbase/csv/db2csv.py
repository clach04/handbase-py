#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
"""sqlite3 or ODBC to CSV that's suitable for Handbase (for Android).

Currently assumes stdout which has implications for locale... This is temporary for debugging purposes!
"""

import csv
import os
import sqlite3
import sys

try:
    #raise ImportError  # DEBUG force pypyodbc usage
    import pyodbc
except ImportError:
    try:
    # try fallback; requires ctypes
        import pypyodbc as pyodbc
    except ImportError:
        pyodbc = None

def con2driver(connection_string):
    if connection_string == ':memory:':
        return sqlite3
    # if looks like path, return sqlite3
    # file.db
    # .\file.db
    # ./file.db
    # /tmp/file.db
    # \tmp\file.db
    # C:\tmp\file.db
    # Z:\tmp\file.db
    # \\some_server\file.db
    if '=' in connection_string:
        return pyodbc
    return sqlite3

def dump_db_to_csv(connection_string, table_name, output_file=sys.stdout, sql=None, db_driver=None):
    db_driver = db_driver or con2driver(connection_string)

    # Assume SQLite3 syntax; db_driver == sqlite3
    sql = sql or 'select * from "%s"' % table_name  # potential for SQL injection shenanigans but we also support arbitary SQL to be passed in already....
    out_csv = csv.writer(output_file)

    con = db_driver.connect(connection_string)
    cur = con.cursor()
    cur.execute(sql)
    column_names = list(x[0] for x in cur.description)
    out_csv.writerow(column_names) 
    row = cur.fetchone()
    while row:
        #print(row)
        out_csv.writerow(row)
        row = cur.fetchone()
    # caller responsible for closing out file...

    cur.close()
    con.commit()
    con.close()



def main(argv=None):
    if argv is None:
        argv = sys.argv

    connection_string = argv[1]
    table_name = argv[2]
    dump_db_to_csv(connection_string, table_name)

    return 0


if __name__ == "__main__":
    sys.exit(main())
