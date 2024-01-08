#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
"""CSV sqlite3 or ODBC to that's suitable for Handbase (for Android) CSV fies.

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


def dump_csv_to_db(csv_filename, connection_string, table_name, param_marker='?', db_driver=sqlite3):
    """Open's named CSV file and uses header as column names.
    Assumes string type for all columns.
    Creates table if not present.
    Appends to table.
    DOES NOT handle NULL values
    Does NOT do any datatype checking. Ideas:
        * scan data keeping stats, then INSERT using best guess heuristic
        * pass in some sort of schema/mapping details
    """
    fh = open(csv_filename, 'r', encoding="cp1252")  # FIXME py3 only

    try:
        in_csv = csv.reader(fh)
        #import pdb ; pdb.set_trace()
        header = next(in_csv)
        num_cols = len(header)
        print(header)
        print('*'*65)
        column_ddl = ', '.join(['%s STRING' % column_name for column_name in header])
        print(column_ddl)
        ddl_sql = 'CREATE TABLE IF NOT EXISTS %s (%s)' % (table_name, column_ddl)  # if table exists, assume correct column names (and we ignore types...)
        print(ddl_sql)
        qmark_bind_markers = ', '.join([param_marker for dummy_values in range(num_cols)])
        column_names = ', '.join(['"%s"' % column_name for column_name in header])
        # assume/use delimited indentifiers
        dml_sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % (table_name, column_names, qmark_bind_markers)  # this is essentially a sanity check on the names
        print(dml_sql)

        con = db_driver.connect(connection_string)
        cur = con.cursor()
        cur.execute(ddl_sql)

        for row in in_csv:
            print(row)
            cur.execute(dml_sql, row)
        cur.close()
        con.commit()
        con.close()

    finally:
        fh.close()


def main(argv=None):
    if argv is None:
        argv = sys.argv

    csv_filename = argv[1]
    connection_string = argv[2]
    table_name = argv[3]
    dump_csv_to_db(csv_filename, connection_string, table_name)

    return 0

if __name__ == "__main__":
    sys.exit(main())
