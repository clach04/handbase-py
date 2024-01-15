# handbase-py

Pure Python 3.x and 2.x code for interacting with HanDBase (for Android).
Home page https://github.com/clach04/handbase-py

The Android version of Handbase has a web interface that offers REST access to some functionality for import/export.

  * TODO limits
  * Encoding; UTF-8 is **NOT** supported. Appears to be latin1 **based**.
    http://www.ddhsoftware.com/knowledgebase.html?read=378&UID=2024010800125198.35.93.189
    claims "Windows Latin 1", this appears to be incorrect as the Euro symbol is safely stored which is not part of latin1, it came much later in [cp1252](https://en.wikipedia.org/wiki/Windows-1252) / [iso 8859-15](https://en.wikipedia.org/wiki/ISO/IEC_8859-15).

Table of Contents

  * [Data and Fields](#data-and-fields)
    + [Limits](#limits)
    + [Datatypes](#datatypes)
      - [Text](#text)
      - [Integer](#integer)
      - [Float](#float)
      - [Pop-Up](#pop-up)
      - [Check-Box](#check-box)
      - [UniqueLegacy](#uniquelegacy)
      - [Signature or Sketch](#signature-or-sketch)
      - [Date](#date)
      - [Time](#time)
      - [Note](#note)
      - [Heading](#heading)
  * [CSV](#csv)
    + [Generating CSV Files Suitable For Import Into Handbase For Android](#generating-csv-files-suitable-for-import-into-handbase-for-android)
    + [Processing CSV Files Exported From Handbase For Android](#processing-csv-files-exported-from-handbase-for-android)

## Data and Fields

### Limits

  * Maximum number of fields 100

### Datatypes

#### Text

Max length 254 characters (actually bytes). Field defintion can limit length.

For missing/empty, empty string is used.

#### Integer

Range appears to be:

  * -1410065407 (-1,410,065,407)
  *  1215752191 (1,215,752,191) == 0x4876E7FF == 0b1001000011101101110011111111111

Can't figure this out

#### Float

Appears to have an option to display digits after the decimal point, 0-4.

Max range unclear

Float-0 Ranges seen:

  * -999999999999999
  * 9000000000000000

Float-4 Ranges seen:

  * -999999999999999
  * 90000000001

#### Pop-Up

When not set, `No Value` - unclear how a string value of same text would work, presumbly treated as NULL/Empty.
Looks like Pop-Up maybe relaetd to DB Pop-UP but this maybe two types? one a lookup the other string where appends/concatenates?
Unclear how Linked Parent/Child work

#### Check-Box

Boolean, in CSV export string `0` is False / UnChecked and `1` is True / Checked.

#### UniqueLegacy

Appears to be an incrementing integer, starting at `1`.

#### Signature or Sketch

Mono / Black and White image. Dimensions/Resolution: guessing 160x160 (original Palm Pilot screen res).

Whilst field/column is included in CSV always empty.

#### Date

Range:
  * 1904-01-02
  * 2031-12-31
also see https://www.ddhsoftware.com/forum/viewtopic.php?f=19&t=4417#p18874

Where values can be manually or automatically set:

  * Date Ask / Manually entered
  * Date Added
  * Date Modified
  * Date Current

Values in CSV of `No Date` indicate NULL/missing.
Format appears to be US format, viz. MM-DD-YYYY example `01/07/2024`.

#### Time

Similar to Date BUT without Current option

  * Time Ask / Manually entered
  * Time Added
  * Time Modified

Values in CSV of `No Time` indicate NULL/missing.

Database does appear to store seconds. CSV does NOT export seconds. this maybe a bug? https://www.ddhsoftware.com/forum/viewtopic.php?p=11228#p11229

Format appears to be AM/PM based, viz. "HH:MM Xm" and whilst the form appear to support/honor seconds CSV export does not. Examples `12:34 pm` and surprisingly `03:50 pm` (i.e., 2 digits for hour, and PM/AM is required) do not confused with 24 Hour format.
UNTESTED sending in 24 hour strings for Handbase to import.


#### Note

Similar to Text but no control over max length. Supports 2000 bytes.

#### Heading

Indicates Column/Field is not used (other than a visual seperate on screen) BUT will show up in CSV export as empty value.

#### Calculated

Can only generate results of types:

  * number (float and pseudo integer)
  * date-only
  * time-only

can perform, for example string concatenation nor extraction. TODO see masks?

https://www.ddhsoftware.com/forum/viewtopic.php?f=6&t=4375#p18739

time is number of seconds for the day for math.

## Demo


1. Download https://www.ddhsoftware.com/gallery.html?show=number&record=1727 Geek_Stuff by E. Cagle
    ASCII character table in HanDBase version 3 format (limited to 7-bit values)

        # upload database, NOTE if already there will DUPLICATE records/rows!
        py  -3 handbase/web/remote.py -u geek_stuff.pdb
        py  -3 handbase/web/remote.py -l
        # see name is different from filename, note double quotes to escape filename spaces
        py  -3 handbase/web/remote.py "Geek Stuff.csv"

2. Download https://www.ddhsoftware.com/gallery.html?show=number&record=802 Wines of Spain by Francis Torres IllescasL
    contains non-ascii characters

    # upload database, NOTE if already there will DUPLICATE records/rows!
    py  -3 handbase/web/remote.py -u vinos3.pdb
    # list databases
    py  -3 handbase/web/remote.py -l
    # download CSV
    py  -3 handbase/web/remote.py vinos3.csv
    # convert into SQLite3 database, with correct encoding (utf-8)
    py -3 handbase/csv/csv2db.py  vinos3.csv -d vinos3.sqlite3 -t vinos3
    # convert back into CSV
    py -3 handbase/csv/db2csv.py vinos3.sqlite3 vinos3 >test.csv  # FIXME Windows issues, make output a filename parameter

## Web Access

### Listing databases

    py  -3 handbase/web/remote.py --ls

### Downloading databases/csv

    py  -3 handbase/web/remote.py DBNAME.csv
    py  -3 handbase/web/remote.py DBNAME.pdb

### Uploading databases/csv

    py  -3 handbase/web/remote.py -u demo.csv

## CSV

Double quotes are NOT required unless data needs to be escaped. Data that needs escaping:
  * newlines
  * double quotes `"`

Handbase expects a header line.

Encoding; UTF-8 is **NOT** supported. Appears to be latin1 based TODO find Palm pdb notes on character sets.

Checkbox False values are exported as `0` and True values are exported as `1`.

Python csv module `writerow()` works fine with Handbase without any extra flags.

### Generating CSV Files Suitable For Import Into Handbase For Android

Demo SQLite3 database, exported in a format suitable for Handbase on Android to be imported via the web interface.

    sqlite3 somedb.sqlite3 < demo.sql
    py -3 ./handbase/csv/db2csv.py somedb.sqlite3 quotes
    py -3 ./handbase/csv/db2csv.py somedb.sqlite3 quotes > demo.csv  # FIXME needs work under Windows, works fine under Linux

When imported using http://androidphone:8000/csv_import.html into a new table should end up with two fields named to match the original schema both set to the TEXT datatype, with max length of "quote" to 71 (which matches the max string length in the demo).
Try updating the 2nd column type to "Check-Box".

NOTE incomplete! Does not handle:

  * file/string encoding
  * NULL values
  * **Any datatypes**, it handles strings (and does not warn about truncation, see note about encoding) and integers to some extent (no warings about truncated/unsupported values)
  * Maximum number of fields check


### Processing CSV Files Exported From Handbase For Android

Assuming demo above has been ran already and have a file called `demo.csv`:

    python handbase/csv/csv2db.py demo.csv -d test_delme.sqlite3 -t quotes
    python2 handbase/csv/csv2db.py demo.csv -d test_delme.sqlite3 -t quotes
    python3 handbase/csv/csv2db.py demo.csv -d test_delme.sqlite3 -t quotes
    py -3 handbase/csv/csv2db.py demo.csv -d test_delme.sqlite3 -t quotes
    sqlite3 test_delme.sqlite3 .dump

## HanDBase PDB

  * datatypes
      * appears to store integers as little-endian. I.e. storing 0x3eadbeef (1051573999) ends up with 0xefbead3e
      * appears to store floats as strings
          - still confused over ranges here and format.
          - **Maybe** limited to 16 bytes storage (including negative sign, decimal marker (TBD, probably `.`)
          - also need to worry about in memory representation and rounding that it performs
      * **Assuming** pop-ups treated as integer index to Pop-Up list/array
      * **Assuming** Check-Box treated as (single-byte) integer
      * **TODO** date
      * **TODO** time
  * delete records appear to be cleared out and not left remaining in the pdb.
  * debian file (filemagic) can not id a HanDBase pdb file, reports it as "data"
  * head of file appears to be the database name (and some sort of meta data) in fixed format (NUL terminated/filled)
      * `HanDHanD` at offset 0x3c (60)
      * `HanDB` variable location, around offset 0x3c0 - 0x3d0
          * after this section field/column metadata present
  * there are 20 instances of a byte sequence which looks like an extract of the 7-bit US-ASCII table, but it is truncated, " !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[/]^_`abc"
      * Some **maybe** related to Views/Forms?
  * `pdblb` shows up a few times as some sort of seperator, **probably NOT** related to number of fields/columns in one table with 16-17 columns saw occurence count=11. For 2 column table (2 rows) saw 4 times.
      * Seen within a few bytes of pop-up values list values
      * **Consistently** seen within a few bytes of *each* row record
      * Seen before ONE buffer of Note (2000) field data (maybe related to Signature/Drawing/Sketch)... but not consistently. Seen before empty/null Note (2000) but also NOT seen before Note (2000) buffer
