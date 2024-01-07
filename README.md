# handbase-py

Pure Python code for interacting with Handbase (for Android).

The Android version of Handbase has a web interface that offers REST access to some functionality for import/export.

  * TODO limits
  * Encoding; UTF-8 is **NOT** supported. Appears to be latin1 based TODO find Palm pdb notes on character sets.

## CSV

Double quotes are NOT required unless data needs to be escaped. Data that needs escaping:
  * newlines
  * double quotes `"`

Handbase expects a header line.

Encoding; UTF-8 is **NOT** supported. Appears to be latin1 based TODO find Palm pdb notes on character sets.

Checkbox True values are exported as `1`.

Python csv module `writerow()` works fine with Handbase without any extra flags.

### CSV Import
### CSV Export

