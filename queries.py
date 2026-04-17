
from db import conectar

def buscar_clientes():

    con = conectar()
    cur = con.cursor()

    sql = """
        select firma,ender,bairro,cid from cadfir
        
    """

    cur.execute(sql)

    colunas = [desc[0] for desc in cur.description]

    dados = []

    for row in cur.fetchall():
        dados.append(dict(zip(colunas, row)))

    con.close()

    return dados

def montar_lista(dados, campo):
    return [r[campo] for r in dados]

CONFIG_RELATORIOS = {
    "saldo_estoque": {
        "sql_base": "relatorios/saldo_estoque.sql",
        "filtros": [
            {
                "tipo": "data_range",
                "campo": "c.dtemis",
                "label": "Período de Movimentação"
            },
            {
                "tipo": "empresa",
                "campo": "c.codemp"
            }
        ]
    },
    "contas_pagar": {
        "sql_base": "relatorios/contas_pagar.sql",
        "filtros": [
            {"tipo": "data_range", "campo": "vencimento"},
            {"tipo": "data_range", "campo": "pagamento"}
        ]
    }
}

def montar_where(filtros_config, params):
    where = []
    valores = {}

    for f in filtros_config:
        campo = f["campo"]

        if f["tipo"] == "data_range":
            di = params.get("data_inicial")
            df = params.get("data_final")

            if di and df:
                where.append(f"{campo} BETWEEN :data_ini AND :data_fim")
                valores["data_ini"] = di
                valores["data_fim"] = df

        elif f["tipo"] == "empresa":
            emp = params.get("empresa")
            if emp:
                where.append(f"{campo} = :empresa")
                valores["empresa"] = emp

    return where, valores

def executar_relatorio(nome_relatorio, params):
    config = CONFIG_RELATORIOS[nome_relatorio]

    with open(config["sql_base"], "r") as f:
        sql = f.read()

    where, valores = montar_where(config["filtros"], params)

    if where:
        if "WHERE" in sql.upper():
            sql += " AND " + " AND ".join(where)
        else:
            sql += " WHERE " + " AND ".join(where)

    return sql, valores