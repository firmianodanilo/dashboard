import fdb

con = fdb.connect(
    dsn='c:/integraw/integraw.fdb',
    user='SYSDBA',
    password='masterkey',
       
)

cur = con.cursor()

cur.execute("SELECT * FROM CADFIR")

for row in cur.fetchall():
    print(row)
