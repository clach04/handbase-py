"""HanDBase internal format details

Example:

    filename = 'Untitled.PDB'
    f = open(filename, 'rb')
    data = f.read()
    f.close()

    metadata = extract_metadata(data)
    #print('%r' % metadata)
    print('%s' % json.dumps(metadata, indent=4))
    print('%d Columns' % len(metadata['columns']))

    print('-' * 65)
    metadata = extract_metadata(data, include_unused=False, include_heading=False)
    sql_ddl = meta2sql_ddl(metadata)
    print('%s' % sql_ddl)

"""

import json
import os
import struct
import sys

is_py3 = sys.version_info >= (3,)

max_field_length = len('Field 1 mmmmmmmmmmm')  # table/database and field/column

HANDBASE_TYPE_UNUSED = 'UNUSED'
HANDBASE_TYPE_TEXT = 'Text'
HANDBASE_TYPE_INTEGER = 'Integer'
HANDBASE_TYPE_FLOAT = 'Float'
HANDBASE_TYPE_POPUP = 'Pop-Up'
HANDBASE_TYPE_CHECKBOX = 'Check-Box'
HANDBASE_TYPE_UNIQUELEGACY = 'UniqueLegacy'
HANDBASE_TYPE_SKETCH = 'Signature or Sketch'
HANDBASE_TYPE_DATE = 'Date'
HANDBASE_TYPE_TIME = 'Time'
HANDBASE_TYPE_NOTE = 'Note'
HANDBASE_TYPE_HEADING = 'Heading'
HANDBASE_TYPE_CALCULATED = 'Calculated'
## TODO relationships / FK
datatypes = {
    0x00: HANDBASE_TYPE_UNUSED,
    0x01: HANDBASE_TYPE_TEXT,  # with length
    0x02: HANDBASE_TYPE_INTEGER,  # little endian storage - odd byes, not full range
    0x03: HANDBASE_TYPE_FLOAT,  # string storage
    0x04: HANDBASE_TYPE_POPUP,  # string like or enum?
    0x05: HANDBASE_TYPE_CHECKBOX,  # 'boolean'

    0x08: HANDBASE_TYPE_DATE,
    0x09: HANDBASE_TYPE_TIME,

    0x0d: HANDBASE_TYPE_HEADING,
    0x0c: HANDBASE_TYPE_NOTE,  # up to 2000 bytes
}

datatypes_to_sql = {
    HANDBASE_TYPE_HEADING: 'dummy_unused_heading',  # REMOVE this if do not want dummy columns
    HANDBASE_TYPE_TEXT: 'varchar',
    HANDBASE_TYPE_NOTE: 'varchar',
    HANDBASE_TYPE_POPUP: 'string',
    HANDBASE_TYPE_INTEGER: 'integer',
    HANDBASE_TYPE_FLOAT: 'float',
    HANDBASE_TYPE_CHECKBOX: 'bool',
    HANDBASE_TYPE_DATE: 'date',
    HANDBASE_TYPE_TIME: 'time',
}

def nul_terminated_bytes_to_string(in_bytes):
    print('DEBUG %r' % in_bytes)
    in_bytes = in_bytes.replace(b'\x00', b'')
    return in_bytes.decode('cp1252')

def single_byte_to_int(in_byte):
    # use struct...
    #return struct.unpack('B', in_byte)[0]  # py2 only
    #return int(in_byte)  # only works for Py3
    #return ord(in_byte)  # only works for Py2
    if is_py3:
        return int(in_byte)
    else:
        # assume py2
        return ord(in_byte)


def extract_metadata(data, number_of_columns=100, include_unused=True, include_heading=True):
    """Has no idea about field/column order and instead relies on physical column order
    TODO include_unused and include_heading would likely need to include column number in result set
    returns dictionary:
        {
            "table_name": "Table Name, max 19 bytes"
            "columns": [
                [
                    "First Field/Column Table Name, max 19 bytes",
                    int,  # HanDBase internal number
                    "Text name of type",  # HanDBase data type name
                    int  # length
                ],
                [
                    "Second Field/Column Table Name, max 19 bytes",
                ...
            ]
        }
    """
    #include_unused = False
    #include_heading = False
    result = {'columns': []}
    table_name = nul_terminated_bytes_to_string(data[0:max_field_length])
    result['table_name'] = table_name
    offset = 1599  # FIXME this offset only seems to work for the reverse enginneered database I created from Android
    segment_length = 97 + max_field_length
    for column_number in range(1, number_of_columns+1):
        record_data = data[offset:offset+segment_length]
        column_datatype = single_byte_to_int(record_data[0])
        column_length = single_byte_to_int(record_data[2])  # only for text (not note)?
        column_name = nul_terminated_bytes_to_string(record_data[0x41:0x41+max_field_length])  # NOTE it is possible the length is actually 20 and nul terminated
        offset += segment_length
        #print('column_name: %r' % (column_name, ))
        #print('type: %s' % (datatypes[column_datatype], ))
        #print('length (if relavent): %d' % (column_length, ))
        if datatypes[column_datatype] == HANDBASE_TYPE_UNUSED and not include_unused:
            continue
        if datatypes[column_datatype] == HANDBASE_TYPE_HEADING and not include_heading:
            continue
        result['columns'].append((column_name, column_datatype, datatypes[column_datatype], column_length))
    return result

def meta2sql_ddl(metadata, table_name=None):
    table_name = table_name or metadata['table_name']
    result = ['CREATE TABLE "%s" (' % table_name]
    sql_types = []
    for column in metadata['columns']:
        column_name, column_datatype, column_datatype_text, column_length = column
        if column_datatype_text == HANDBASE_TYPE_NOTE:
            column_length = 2000
        elif column_datatype_text != HANDBASE_TYPE_TEXT:
            column_length = None
        sql_type = datatypes_to_sql[column_datatype_text]
        if column_length:
            sql_type = sql_type + '(%d)' % column_length
        sql_types.append('    "%s" %s' % (column_name, sql_type))  # TODO NOT NULL/nullable, default value....
    result.append(',\n'.join(sql_types))
    result.append(');')
    # Guess PK? indexes...
    return '\n'.join(result)
