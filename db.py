import fdb

def conectar():

    con = fdb.connect(
        dsn='10.0.0.2:C:/integraw/integraw.fdb',
        user='SYSDBA',
        password='masterkey',
        charset='UTF8',
        
    )

    return con
