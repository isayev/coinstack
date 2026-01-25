import sqlite3
conn = sqlite3.connect('coinstack_v2.db')
for row in conn.execute(\
SELECT
name
FROM
sqlite_master
WHERE
type=table\):
    print(row[0])
