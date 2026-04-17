import fdb

def conectar():

    con = fdb.connect(
        dsn='10.0.0.2/3050:c:/integraw/integraw.fdb',
        user='SYSDBA',
        password='masterkey',
        charset='UTF8',
        sql_dialect=3        
    )

    return con
