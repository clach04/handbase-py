#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
"""Handbase (for Android) remote Web access

"""

import logging
import os
from optparse import OptionParser
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

__version__ = '0.0.0'

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

    log.debug('about to get %r', get_db_url)
    f = urlopen(get_db_url)
    result = f.read()
    #print('result: %r' % result)
    log.debug('Got %r', result)
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
    dbcontent - database content in bytes. Either HanDBase v4.x PDB or CSV (in Windows-1252/cp1252 encoding)

    TODO check header of dbcontents looks reasonable, e.g. PDB check
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


class MyOptionParser(OptionParser):
    pass
    """
    def format_epilog(self, formatter):
        log.debug('formatter %r', formatter)
        log.debug('epilog %r', self.epilog)
        #return self.expand_prog_name(self.epilog)
        return self.epilog
    """


def main(argv=None):
    if argv is None:
        argv = sys.argv

    usage = "usage: %prog [options] filename"
    description = '''Interact with HanDBase web server

Examples:

    %prog -u mydb.pdb  # upload HandDBase db, from file mydb.pdb
    %prog -u mydb.csv  # upload csv, from file mydb.csv - defaults database name
    %prog -u mydb.csv -d my_db_name  # upload csv, from file mydb.csv - into specified database name

    %prog  mydb.pdb  # download HandDBase db, into file mydb.pdb - defaults database name to mydb
    %prog  mydb.csv  # download csv, into file mydb.csv - defaults database name to mydb
    %prog  mydb.csv -d my_db_name  # download csv, into file mydb.csv - from specified database name
'''
    parser = MyOptionParser(usage=usage, version="%%prog %s" % __version__, description=description)
    parser.add_option("-d", "--dbname", help="Database/table name, if not set defaults based on filename")
    parser.add_option("-l", "--ls", "--list", help="List databases TODO", action="store_true")
    parser.add_option("-u", "--upload", help="Upload a file", action="store_true")
    parser.add_option("--url", help="Specify server URL, if not set checks HANDBASE_URL os env, defaults to http://localhost:8000")
    parser.add_option("-v", "--verbose", help='Verbose', action="store_true")

    (options, args) = parser.parse_args(argv[1:])
    verbose = options.verbose
    if verbose:
        print('Python %s on %s' % (sys.version.replace('\n', ' - '), sys.platform))

    print('options: %r' % options)
    print('args: %r' % args)
    print('dbname: %r' % options.dbname)
    print('ls: %r' % options.ls)
    print('upload: %r' % options.upload)
    print('url: %r' % options.url)

    server_url = options.url or os.environ.get('HANDBASE_URL', 'http://localhost:8000')  # alternative idea; if not set, stop here
    print('Using server: %s' % server_url)

    if options.ls:
        raise NotImplementedError('list support TODO')

    filename = args[0]  # looks like case may is NOT be significant to server (for download or upload)
    print('filename: %r' % filename)

    dbname = options.dbname or filename.rsplit('.', 1)[0]
    print('dbname: %r' % dbname)

    dbtype = DBTYPE_CSV
    if filename.lower().endswith('.pdb'):
        dbtype = DBTYPE_PDB

    #raise Shields
    if options.upload:
        f = open(filename, 'rb')
        csv_bytes = f.read()
        f.close()
        put_db(server_url, dbname, csv_bytes, dbtype=dbtype)
    else:  # download (default)
        returned_filename, filecontents = get_db(server_url, dbname, dbtype=dbtype)
        #print((filename, returned_filename, filecontents))  # TODO save to disk
        f = open(filename, 'wb')  # user specified filename
        f.write(filecontents)
        f.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
