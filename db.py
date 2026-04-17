import fdb

def conectar():

    con = fdb.connect(
        dsn='C:/integraw/integraw.fdb',
        user='SYSDBA',
        password='masterkey',
        charset='UTF8',
        
    )

    return con
