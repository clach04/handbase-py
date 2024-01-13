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


def dumb_html_table_string_extract(line):
    # line needs to contain a single line, no newlines
    tmp_str = line[line.find('>') + 1:]
    tmp_str = tmp_str[:tmp_str.find('<')]
    return tmp_str

def dumb_handbase_parser_printer(html):
    """This is EXTREMELY fragile and dependent on how HanDBase 4.x under Androoud displays its index.html
    """
    handbase_table_start_marker = '<table'
    handbase_table_end_marker = '</table>'

    table_str = html[html.find(handbase_table_start_marker):]
    table_str = table_str[:table_str.find(handbase_table_end_marker)]

    #print('table_str %r' % table_str)
    #print('-' * 65)
    #print('%s' % table_str)
    #print('-' * 65)
    table_details = []
    table_list = []
    for line in table_str.split('\n'):
        #if ' class="thbody">' in line:
        #if ' class="tdbody">' in line:
        if ' class="tdbody">' in line or ' class="thbody">' in line:
            #print('%s' % line)
            #print('%s' % dumb_html_table_string_extract(line))
            table_details.append(dumb_html_table_string_extract(line))
        elif '</tr>' in line:
            header_row = False
            if table_details == ['Database', 'Date/Time', 'File Size', 'Records', 'Download']:
                header_row = True
            #print(table_details)
            tmp = table_details.pop(0)
            table_details.append(tmp)
            if header_row:
                table_details[1] = '\t\t' + table_details[1]
                del table_details[3]
            else:
                # TODO formatting of date into ISO
                table_details[2] = '\t' + table_details[2]
                table_list.append(table_details[-1])
            #print(table_details)
            print('\t'.join(table_details))
            #print('')
            table_details = []
    return table_list

def get_db_list(server_url):
    """Returns list of databases
    """
    if not server_url.endswith('/'):
        server_url += '/'

    get_db_list_url = server_url  #+ 'export.csv?db=' + server_dbname

    f = urlopen(get_db_list_url)
    result = f.read()
    #log.debug('Got %r', result)
    # TODO parse table....
    table_list = dumb_handbase_parser_printer(result)
    return table_list

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

    #print((put_db_url, dbname, dbcontent, dbtype))
    print((put_db_url, dbname, len(dbcontent), dbtype))

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

    headers = {'content-type': content_type, 'content-length': len(body)}
    log.debug('headers %r', headers)
    put_url(put_db_url, body, headers=headers, verb=POST)


class MyOptionParser(OptionParser):
    def format_epilog(self, formatter):
        return self.expand_prog_name(self.epilog)

def filename2dbname(filename):
    dbname = filename.replace('\\', '/')
    if '/' in dbname:
        dbname = dbname.rsplit('/', 1)[1]
    dbname = dbname.rsplit('.', 1)[0]
    return dbname

def main(argv=None):
    if argv is None:
        argv = sys.argv

    usage = "usage: %prog [options] filename"
    description = '''Interact with HanDBase web server'''
    example_usage = '''
Examples:

    %prog -u mydb.pdb  # upload HandDBase db, from file mydb.pdb
    %prog -u mydb.csv  # upload csv, from file mydb.csv - defaults database name
    %prog -u mydb.csv -d my_db_name  # upload csv, from file mydb.csv - into specified database name

    %prog  mydb.pdb  # download HandDBase db, into file mydb.pdb - defaults database name to mydb
    %prog  mydb.csv  # download csv, into file mydb.csv - defaults database name to mydb
    %prog  mydb.csv -d my_db_name  # download csv, into file mydb.csv - from specified database name
'''
    parser = MyOptionParser(usage=usage, version="%%prog %s" % __version__, description=description, epilog=example_usage)
    parser.add_option("-d", "--dbname", help="Database/table name, if not set defaults based on filename")
    parser.add_option("-l", "--ls", "--list", help="List databases TODO", action="store_true")
    parser.add_option("-u", "--upload", help="Upload a file", action="store_true")
    parser.add_option("--url", help="Specify server URL, if not set checks HANDBASE_URL os env, defaults to http://localhost:8000")
    parser.add_option("-v", "--verbose", help='Verbose', action="store_true")

    (options, args) = parser.parse_args(argv[1:])
    if not args:
        ## TODO consider using something line https://stackoverflow.com/a/664614 to add positional argument support
        parser.print_help()
        print('\n MISSING filename')  # stderr?
        return 1

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
        database_list = get_db_list(server_url)
        print('database_list %r' % database_list)
        return 0

    filename = args[0]  # looks like case may is NOT be significant to server (for download or upload)
    print('filename: %r' % filename)

    #dbname = options.dbname or filename.rsplit('.', 1)[0]
    dbname = options.dbname or filename2dbname(filename)
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
        save_content = False
        if dbtype == DBTYPE_CSV:
            if filecontents.strip():
                save_content = True
        else:
            if len(filecontents) > 30:
                save_content = True

        if save_content:
            f = open(filename, 'wb')  # user specified filename
            f.write(filecontents)
            f.close()
        else:
            log.info('NOT saving, result empty/too-small %d bytes', len(filecontents))

    return 0


if __name__ == "__main__":
    sys.exit(main())
