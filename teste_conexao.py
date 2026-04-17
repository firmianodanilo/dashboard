import fdb

con = fdb.connect(
    dsn='c:/integraw/integraw.fdb',
    user='SYSDBA',
    password='masterkey',
    fb_library_name='/usr/lib/x86_64-linux-gnu/libfbclient.so'   
)

cur = con.cursor()

cur.execute("SELECT * FROM CADFIR")

for row in cur.fetchall():
    print(row)
