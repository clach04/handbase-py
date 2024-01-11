#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
"""Handbase (for Android) remote Web access

"""

import os
import sys

try:
    # Py3
    from urllib.error import HTTPError
    from urllib.request import build_opener, urlopen, urlretrieve, HTTPBasicAuthHandler, HTTPDigestAuthHandler, HTTPPasswordMgrWithDefaultRealm, Request
    from urllib.parse import parse_qs, quote_plus, urlencode, urljoin, urlparse
except ImportError:
    # Py2
    from cgi import parse_qs  # py2 (and <py3.8)
    from urlparse import urljoin, urlparse
    from urllib import quote_plus, urlencode, urlretrieve  #TODO is this in urllib2?
    from urllib2 import build_opener, urlopen, HTTPBasicAuthHandler, HTTPDigestAuthHandler, HTTPPasswordMgrWithDefaultRealm, Request, HTTPError


DBTYPE_PDB = 'PDB'
DBTYPE_CSV = 'CSV'
PDB_EXTENSION = '.PDB'  # case significant, for url?
CSV_EXTENSION = '.csv'

def get_db(server_url, dbname, dbtype=DBTYPE_CSV):
    """Returns tuple of; filename, contents.
    Where contents is bytes, csv will be cp1252 encoded
    """
    if not server_url.endswith('/'):
        server_url += '/'

    server_dbname = dbname + PDB_EXTENSION

    if dbtype == DBTYPE_CSV:
        get_db_url = server_url + 'export.csv?db=' + server_dbname
        result_filename = dbname + CSV_EXTENSION  # default from server is 'export.csv'
    elif dbtype == DBTYPE_PDB:
        get_db_url = server_url +server_dbname
        result_filename = dbname + PDB_EXTENSION
    else:
        raise NotImplementedError('dbtype=%r' % dbtype)

    print(get_db_url)
    f = urlopen(get_db_url)
    result = f.read()
    #print('result: %r' % result)
    return (result_filename, result)


def main(argv=None):
    if argv is None:
        argv = sys.argv

    server_url = os.environ.get('HANDBASE_URL', 'http://localhost:8000')  # alternative if not set, stop here
    dbname = argv[1]  # looks like case may not be NOT be significant
    dbtype = DBTYPE_CSV
    try:
        if argv[1].lower() == 'pdb':
            dbtype = DBTYPE_PDB
    except IndexError:
        pass

    filename, filecontents = get_db(server_url, dbname, dbtype=dbtype)
    print((filename, filecontents))  # TODO save to disk

    return 0


if __name__ == "__main__":
    sys.exit(main())
