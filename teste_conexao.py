import fdb

con = fdb.connect(
    dsn='c:/integraw/integraw.fdb',
    user='SYSDBA',
    password='masterkey',
     fb_library_name=r"C:\Program Files\Firebird\Firebird_2_5\bin\fbclient.dll"
   
)

cur = con.cursor()

cur.execute("SELECT * FROM CADFIR")

for row in cur.fetchall():
    print(row)