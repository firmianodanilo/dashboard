import fdb

def conectar():

    con = fdb.connect(
        dsn='C:/integraw/integraw.fdb',
        user='SYSDBA',
        password='masterkey',
        charset='UTF8',
        fb_library_name=r"C:\Program Files\Firebird\Firebird_2_5\bin\fbclient.dll"
    )

    return con