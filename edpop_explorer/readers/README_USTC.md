USTC is implemented as a SQLite3 database, which the user has to download
before usage. The file is considerably large (370 MiB) so that a download
on the fly is not provided (contrary to FBTEE, where the file is automatically
downloaded).

We receive USTC as a Microsoft Access database - currently only the Editions
table. This can be converted to a SQLite3 database as follows:

* Export the table to CSV format inside Microsoft Access
* Fix encoding issues and convert to `utf-8`:

  contents = open('<filename>.csv', 'rb').read() \
      .decode('cp1252', errors='ignore')
  open('<filename>-v2.csv', 'w').write(contents)

* Convert to SQLite3 using `pandas` (`pandas` appears to be reading the file
  without issues, except for one invalid line in my case)

  import pandas as pd
  data = pd.read_csv(
      '<filename>-v2.csv',
      sep=';',
      on_bad_lines='warn',
      low_memory=False
  )
  import sqlite3
  cnx = sqlite3.connect('ustc.sqlite3')
  data.to_sql(name='editions', con=cnx)

This creates the database `ustc.sqlite3` with the table `editions`. This file
can be put into the location that `USTCReader` will point at when run.
