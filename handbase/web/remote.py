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

## TODO hand send_db()
# MAX_FILE_SIZE=3000000
# localfile
#
# /csv_import.html - appletname
# /applet_add.html
def put_db(server_url, dbname, dbcontent, dbtype=DBTYPE_CSV):
    """
    dbname - name withOUT extension
    dbcontent - database content in bytes
    """
    if not server_url.endswith('/'):
        server_url += '/'

    post_dict = {
        'MAX_FILE_SIZE': '3000000',
        'appletname': dbname,
        'localfile': dbcontent,
    }

    if dbtype == DBTYPE_CSV:
        put_db_url = server_url + 'csv_import.html'
        post_dict['UpCSV'] = 'Add CSV Data'
        post_dict['filename'] = dbname + CSV_EXTENSION
    elif dbtype == DBTYPE_PDB:
        put_db_url = server_url + 'applet_add.html'
        post_dict['UpPDB'] = 'Add File'
        post_dict['filename'] = dbname + PDB_EXTENSION
    else:
        raise NotImplementedError('dbtype=%r' % dbtype)

    print((put_db_url, dbname, dbcontent, dbtype))
    # there mimetype / Content-Type
    '''http://localhost:8000/uploadfile.html

Content-Disposition: form-data; name="localfile"; filename="demo.csv"\r\nContent-Type: text/csv\r\n
body payload: b'------WebKitFormBoundaryYh9PyfUKEduVZ1nE\r\nContent-Disposition: form-data; name="MAX_FILE_SIZE"\r\n\r\n3000000\r\n------WebKitFormBoundaryYh9PyfUKEduVZ1nE\r\nContent-Disposition: form-data; name="appletname"\r\n\r\nMyDemoCSV\r\n------WebKitFormBoundaryYh9PyfUKEduVZ1nE\r\nContent-Disposition: form-data; name="localfile"; filename="demo.csv"\r\nContent-Type: text/csv\r\n\r\nquote,nsfw\r\n"""Off with his head!"", the Queen said.",0\r\nIt\'s the luck of the Irish!,0\r\n"Expletive-deleted, expletive-deleted you expletive-deleted.",1\r\n"This is a teeny, tiny bit longer than sixty bytes/characters.",0\r\n"Ready?\r\nSteady?\r\nGo!",0\r\n"Annother.\r\nNewline?\r\nDemo.",0\r\n\r\n------WebKitFormBoundaryYh9PyfUKEduVZ1nE\r\nContent-Disposition: form-data; name="UpCSV"\r\n\r\nAdd CSV Data\r\n------WebKitFormBoundaryYh9PyfUKEduVZ1nE--\r\n'


Content-Disposition: form-data; name="localfile"; filename="truncated_test.pdb"\r\nContent-Type: application/octet-stream\r\n
payload: b'------WebKitFormBoundaryOLAJZSjCrK53Sqs8\r\nContent-Disposition: form-data; name="MAX_FILE_SIZE"\r\n\r\n3000000\r\n------WebKitFormBoundaryOLAJZSjCrK53Sqs8\r\nContent-Disposition: form-data; name="localfile"; filename="truncated_test.pdb"\r\nContent-Type: application/octet-stream\r\n\r\ntest\x00\x00....\r\n------WebKitFormBoundaryOLAJZSjCrK53Sqs8\r\nContent-Disposition: form-data; name="UpPDB"\r\n\r\nAdd File\r\n------WebKitFormBoundaryOLAJZSjCrK53Sqs8--\r\n'


NON db content
request_body is b'------WebKitFormBoundaryPorY4DxgZRva13lw\r\nContent-Disposition: form-data; name="MAX_FILE_SIZE"\r\n\r\n3000000\r\n------WebKitFormBoundaryPorY4DxgZRva13lw\r\nContent-Disposition: form-data; name="localfile"; filename="icon.png"\r\nContent-Type: image/png\r\n\r\n\x89PNG\r\n.......`\x82\r\n------WebKitFormBoundaryPorY4DxgZRva13lw\r\nContent-Disposition: form-data; name="UpPDB"\r\n\r\nAdd File\r\n------WebKitFormBoundaryPorY4DxgZRva13lw--\r\n'

    '''

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

    # download
    """
    filename, filecontents = get_db(server_url, dbname, dbtype=dbtype)
    print((filename, filecontents))  # TODO save to disk
    """

    demo_csv = '''quote,nsfw
"""Off with his head!"", the Queen said.",0
It's the luck of the Irish!,0
"Expletive-deleted, expletive-deleted you expletive-deleted.",1
"This is a teeny, tiny bit longer than sixty bytes/characters.",0
"Ready?
Steady?
Go!",0
"Annother.
Newline?
Demo.",0
'''
    dbname = 'delete_me_upload'
    put_db(server_url, dbname, demo_csv, dbtype=DBTYPE_CSV)

    return 0


if __name__ == "__main__":
    sys.exit(main())
