#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
"""CSV to sqlite3 or ODBC to that's suitable for Handbase (for Android) CSV fies.

"""

import codecs  # pre Python 3 support
import csv
from optparse import OptionParser
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

import handbase_format
from db2csv import con2driver

is_py3 = sys.version_info >= (3,)


__version__ = '0.0.0'


def dump_csv_to_db(csv_filename, connection_string, table_name, param_marker='?', db_driver=None, ddl_sql=None, dml_sql=None, encoding='cp1252'):
    """Open's named CSV file and uses header as column names.
    Assumes string type for all columns.
    Creates table if not present.
    Appends to table.
    Partially handles NULL values, does NOT check datatype.
    Does NOT do any datatype checking. Ideas:
        * scan data keeping stats, then INSERT using best guess heuristic
        * pass in some sort of schema/mapping details
    """
    db_driver = db_driver or con2driver(connection_string)

    #encoding = "latin1"
    #encoding = "cp1252"
    #encoding = "utf-8"  # FIXME - I'm injecting utf8 into HanDBase BUT it does not understand it, it treats it like latin-1/15
    if is_py3:
        fh = codecs.open(csv_filename, 'rb', encoding=encoding)
    else:
        fh = open(csv_filename, 'rb')

    try:
        in_csv = csv.reader(fh)
        #import pdb ; pdb.set_trace()
        header = next(in_csv)
        if not is_py3:
            header = [x.decode(encoding) for x in header]
        num_cols = len(header)
        print(header)
        print('*'*65)
        if ddl_sql is None:
            # Assume SQLite3 syntax
            column_ddl = ', '.join(['"%s" STRING' % column_name for column_name in header])
            print(column_ddl)
            ddl_sql = 'CREATE TABLE IF NOT EXISTS %s (%s)' % (table_name, column_ddl)  # if table exists, assume correct column names (and we ignore types...)
        print(ddl_sql)
        if dml_sql is None:
            qmark_bind_markers = ', '.join([param_marker for dummy_values in range(num_cols)])
            column_names = ', '.join(['"%s"' % column_name for column_name in header])
            # assume/use delimited indentifiers
            dml_sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % (table_name, column_names, qmark_bind_markers)  # this is essentially a sanity check on the names
        print(dml_sql)

        con = db_driver.connect(connection_string)
        cur = con.cursor()
        cur.execute(ddl_sql)

        for row_count, row in enumerate(in_csv):
            print('row %d' % row_count)  # TODO verbose logging option
            if not is_py3:
                row = [x.decode(encoding) for x in row]
            #print(repr(row))
            """
            if row[0].startswith('Power drift'):
                import pdb ; pdb.set_trace()
            """
            processed_row = []
            for column in row:
                if column in ('No Date', 'No Time', 'No Value'):
                    # we assume this is a date column TODO check metadata...
                    column = None
                # FIXME handle dates, date format is US, really want iso/ansi format
                processed_row.append(column)
            cur.execute(dml_sql, tuple(processed_row))
        cur.close()
        con.commit()
        con.close()

    finally:
        fh.close()


class MyOptionParser(OptionParser):  # FIXME dupe
    def format_epilog(self, formatter):
        # preserve newlines
        return self.expand_prog_name(self.epilog)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    usage = "usage: %prog [options] filename.csv"
    description = '''CSV2SQLite3'''
    example_usage = '''
Examples:

    %prog TODO
'''
    parser = MyOptionParser(usage=usage, version="%%prog %s" % __version__, description=description, epilog=example_usage)
    parser.add_option("-d", "--dbname", help="SQL (SQLite3) Database name, if not set defaults based on filename.csv")
    parser.add_option("--pdb", help="Optional HanDBase filename, used to generate DDL (data ignored, data comes from CSV)")
    parser.add_option("-t", "--table", help="Table name, if not set defaults based on filename")
    parser.add_option("-e", "--encoding", help="Character encoding. WARNING HanDBase (v4) ONLY supports cp1252, NOT utf-8, only set if you know what you are doing", default='cp1252')
    parser.add_option("-v", "--verbose", help='Verbose', action="store_true")

    (options, args) = parser.parse_args(argv[1:])
    if not args:
        ## TODO consider using something line https://stackoverflow.com/a/664614 to add positional argument support
        parser.print_help()
        print('\n MISSING CSV filename')  # stderr?
        return 1

    verbose = options.verbose
    if verbose:
        print('Python %s on %s' % (sys.version.replace('\n', ' - '), sys.platform))

    print('options: %r' % options)
    print('args: %r' % args)
    print('dbname: %r' % options.dbname)
    print('encoding: %r' % options.encoding)

    csv_filename = args[0]  # looks like case may is NOT be significant to server (for download or upload)
    print('filename: %r' % csv_filename)

    if not options.dbname:
        options.dbname = csv_filename + '.sqlite3'  # TODO remove CSV....
    print('dbname: %r' % options.dbname)

    table_name = options.table
    connection_string = options.dbname

    if options.pdb:
        if table_name:
            table_name_override = table_name
        else:
            table_name_override = None
        f = open(options.pdb, 'rb')
        data = f.read()
        f.close()
        metadata = handbase_format.extract_metadata(data, include_unused=False, include_heading=True)  # they show up in CSV!?
        ddl_sql = handbase_format.meta2sql_ddl(metadata, table_name=table_name_override)
        if table_name is None:
            table_name = metadata['table_name']
    else:
        ddl_sql = None

    if not table_name:
        table_name = 'default_table'  # FIXME, use databasename?

    dump_csv_to_db(csv_filename, connection_string, table_name, ddl_sql=ddl_sql, encoding=options.encoding)

    return 0

if __name__ == "__main__":
    sys.exit(main())
