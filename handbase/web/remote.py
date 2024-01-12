#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
"""Handbase (for Android) remote Web access

"""

import logging
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


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
disable_logging = False
#disable_logging = True
if disable_logging:
    log.setLevel(logging.NOTSET)  # only logs; WARNING, ERROR, CRITICAL

ch = logging.StreamHandler()  # use stdio

formatter = logging.Formatter("logging %(process)d %(thread)d %(asctime)s - %(filename)s:%(lineno)d %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
log.addHandler(ch)



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


POST = 'POST'

def put_url(url, data, headers=None, verb=POST):
    log.debug('put_url %s=%r', verb, url)
    response = None
    try:
        if headers:
            request = Request(url, data=data, headers=headers)
        else:
            request = Request(url, data=data)  # may not be needed
        request.get_method = lambda: verb
        response = urlopen(request)
        url = response.geturl()  # WILL this work?
        code = response.getcode()
        #log("putURL [{}] response code:{}".format(url, code))
        result = response.read()
        return result
    finally:
        if response != None:
            response.close()


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
    }

    if dbtype == DBTYPE_CSV:
        put_db_url = server_url + 'csv_import.html'
        post_dict['UpCSV'] = 'Add CSV Data'
        filename = dbname + CSV_EXTENSION
        file_content_type = 'text/csv'
    elif dbtype == DBTYPE_PDB:
        put_db_url = server_url + 'applet_add.html'
        post_dict['UpPDB'] = 'Add File'
        filename = dbname + PDB_EXTENSION
        file_content_type = 'application/octet-stream'
    else:
        raise NotImplementedError('dbtype=%r' % dbtype)

    print((put_db_url, dbname, dbcontent, dbtype))

    bounder_mark = b'----------BOUNDARY_MARKER_GOES_HERE'
    body_list = []
    for key in post_dict:
        value = post_dict[key]
        body_list.append(b'--' + bounder_mark)
        body_list.append(b'Content-Disposition: form-data; name="%s"' % key)
        body_list.append(b'')
        body_list.append(value)
    # file
    files = [('localfile', filename, dbcontent), ]
    for (key, filename, value) in files:
        body_list.append(b'--' + bounder_mark)
        body_list.append(b'Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        body_list.append(b'Content-Type: %s' % file_content_type)
        body_list.append(b'')
        body_list.append(value)
    body_list.append('--' + bounder_mark + '--')
    body_list.append('')
    body = b'\r\n'.join(body_list)
    content_type = b'multipart/form-data; boundary=%s' % bounder_mark

    headers = {'content-type': content_type, 'content-length': len('content-length')}
    put_url(put_db_url, body, headers=headers, verb=POST)


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
