# handbase-py

Pure Python code for interacting with Handbase (for Android).

The Android version of Handbase has a web interface that offers REST access to some functionality for import/export.

  * TODO limits
  * Encoding; UTF-8 is **NOT** supported. Appears to be latin1 **based**.
    http://www.ddhsoftware.com/knowledgebase.html?read=378&UID=2024010800125198.35.93.189
    claims "Windows Latin 1", this appears to be incorrect as the Euro symbol is safely stored which is not part of latin1, it came much later in [cp1252](https://en.wikipedia.org/wiki/Windows-1252) / [iso 8859-15](https://en.wikipedia.org/wiki/ISO/IEC_8859-15).

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
  *  1215752191 (1,215,752,191)

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

#### Check-Box

Boolean, in CSV export string `0` is False / UnChecked and `1` is True / Checked.

#### UniqueLegacy

Appears to be an incrementing integer, starting at `1`.

#### Signature or Sketch

Mono / Black and White image. Dimensions/Resolution: guessing 160x160 (original Palm Pilot screen res).

Whilst field/column is included in CSV always empty.

#### Date

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

Database does appear to store seconds. CSV does NOT export seconds.

Format appears to be AM/PM based, viz. "HH:MM Xm" and whilst the form appear to support/honor seconds CSV export does not. Examples `12:34 pm` and surprisingly `03:50 pm` (i.e., 2 digits for hour, and PM/AM is required) do not confused with 24 Hour format.
UNTESTED sending in 24 hour strings for Handbase to import.


#### Note

Similar to Text but no control over max length. Supports 2000 bytes.

#### Heading

Indicates Column/Field is not used (other than a visual seperate on screen) BUT will show up in CSV export as empty value.

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

    sqlite3 /tmp/somedb.sqlite3 < demo.sql
    ./handbase/csv/db2csv.py /tmp/somedb.sqlite3 quotes

When imported using http://androidphone:8000/csv_import.html into a new table should end up with two fields named to match the original schema both set to the TEXT datatype, with max length of "quote" to 71 (which matches the max string length in the demo).
Try updating the 2nd column type to "Check-Box".

NOTE incomplete! Does not handle:

  * file/string encoding
  * NULL values
  * **Any datatypes**, it handles strings (and does not warn about truncation, see note about encoding) and integers to some extent (no warings about truncated/unsupported values)
  * Maximum number of fields check


### Processing CSV Files Exported From Handbase For Android

TODO - see notes above.
