from flask import Flask, render_template, request
import os
from db import conectar
from datetime import date, timedelta, datetime

app = Flask(__name__)

PASTA_RELATORIOS = "relatorios"

CONFIG_FILTROS = {
    "saldo_estoque": {
        "usar_tipo_data": False,
        "usar_cliente": False,
        "usar_empresa": True,
        "campo_data": "c.dtemis"
    },
    "contas_pagar": {
        "usar_tipo_data": True,
        "usar_cliente": True,
        "usar_empresa": True
    },
    "contas_receber": {
        "usar_tipo_data": True,
        "usar_cliente": True,
        "usar_empresa": True
    }
}

def montar_filtros(filtros_config, params):
    where = []
    valores = {}

    for filtro in filtros_config:
        campo = filtro["campo"]
        tipo = filtro["tipo"]

        if tipo == "data_range":
            data_ini = params.get("data_inicial")
            data_fim = params.get("data_final")

            if data_ini and data_fim:
                where.append(f"{campo} BETWEEN :data_ini AND :data_fim")
                valores["data_ini"] = data_ini
                valores["data_fim"] = data_fim

        elif tipo == "empresa":
            if params.get("empresa"):
                where.append(f"{campo} = :empresa")
                valores["empresa"] = params["empresa"]

    return where, valores
def montar_filtro(empresas):
    if empresas:
        lista = ",".join([f"'{e}'" for e in empresas])
        return f"AND f.firma IN ({lista})"
    return ""

def dados_plano():

    con = conectar()
    cur = con.cursor()

    cur.execute("""
        SELECT 
            p.descr AS plano,
            SUM(CASE WHEN m.tipomov = 'E' THEN m.valor ELSE 0 END) AS entrada,
            SUM(CASE WHEN m.tipomov = 'S' THEN m.valor ELSE 0 END) AS saida
        FROM movban m
        LEFT JOIN cadplb p ON p.codpla = m.codpla
        GROUP BY p.descr
    """)

    planos = []
    entrada = []
    saida = []

    for plano, ent, sai in cur.fetchall():
        planos.append(plano)
        entrada.append(float(ent or 0))
        saida.append(float(sai or 0))

    con.close()

    return planos, entrada, saida

def dados_banco(data_ini, data_fim, empresas):
    filtro = montar_filtro(empresas)

    con = conectar()
    cur = con.cursor()

    sql = f"""
        SELECT 
            f.firma AS banco,
            SUM(m.valor) AS total
        FROM movban m
        LEFT JOIN cadfir f ON f.codfir = m.codfir
        WHERE m.dtemis BETWEEN '{data_ini}' AND '{data_fim}'
        {filtro}
        GROUP BY f.firma
    """

    cur.execute(sql)

    bancos = []
    valores = []

    for banco, total in cur.fetchall():
        bancos.append(banco)
        valores.append(float(total or 0))

    con.close()

    return bancos, valores

def total_pendente(data_ini, data_fim, empresas):
    filtro = montar_filtro(empresas)

    con = conectar()
    cur = con.cursor()

    sql = f"""
    SELECT
        COALESCE(SUM(CASE WHEN m.tipomov = 'E' THEN m.valor END),0) -
        COALESCE(SUM(CASE WHEN m.tipomov = 'S' THEN m.valor END),0)
    FROM movban m
    LEFT JOIN cadfir f ON f.codfir = m.codfir
    WHERE m.dtban IS NULL
    AND m.dtemis BETWEEN '{data_ini}' AND '{data_fim}'
    {filtro}
    """


    cur.execute(sql)

    resultado = cur.fetchone()[0] or 0

    con.close()

    return f"{float(resultado):,.2f}"

    

def total_conciliado(data_ini, data_fim, empresas):
    filtro = montar_filtro(empresas)

    con = conectar()
    cur = con.cursor()

    sql = f"""
    SELECT
        COALESCE(SUM(CASE WHEN m.tipomov = 'E' THEN m.valor END),0) -
        COALESCE(SUM(CASE WHEN m.tipomov = 'S' THEN m.valor END),0)
    FROM movban m
    LEFT JOIN cadfir f ON f.codfir = m.codfir
    WHERE m.dtban IS NOT NULL
    AND m.dtemis BETWEEN '{data_ini}' AND '{data_fim}'
    {filtro}
    """

    cur.execute(sql)

    resultado = cur.fetchone()[0] or 0

    con.close()

    return f"{float(resultado):,.2f}"

def vendas_mensal(data_ini, data_fim, empresas):
    filtro = montar_filtro(empresas)

    con = conectar()
    cur = con.cursor()

    
    sql = f"""
    SELECT
        EXTRACT(MONTH FROM m.dtemis) AS mes,
        SUM(COALESCE(m.totdoc, 0)) AS total
    FROM movclic m
    INNER JOIN cadfisc fi
        ON fi.coddepf = m.coddepf
    AND fi.codbon = m.codbon
    LEFT JOIN cadfir f ON f.codfir = m.codfir
    WHERE m.dtemis BETWEEN '{data_ini}' AND '{data_fim}'
    AND fi.efatura = 'S'
    {filtro}
    GROUP BY mes
    """

    cur.execute(sql)

    dados = {i: 0 for i in range(1, 13)}

    for mes, valor in cur.fetchall():
        dados[int(mes)] = float(valor or 0)

    con.close()

    return [dados[i] for i in range(1, 13)]

def seguro_float(valor):
    try:
        return float(valor)
    except:
        return 0

def resumo_receber(data_ini, data_fim, empresas):
    filtro = montar_filtro(empresas)

    con = conectar()
    cur = con.cursor()

    sql = f"""
    SELECT dtvenc, dtpg, valor, vrpg
    FROM movcr m
    LEFT JOIN cadfir f ON f.codfir = m.codfir
    WHERE m.dtvenc BETWEEN '{data_ini}' AND '{data_fim}'
    {filtro}
    """

    cur.execute(sql)
    


    hoje = date.today()

    recebidos = 0
    atrasados = 0
    hoje_venc = 0
    futuros = 0

    for dtvenc, dtpg, valor, vrpg in cur.fetchall():

        valor = float(valor or 0)
        vrpg = float(vrpg or 0)

        # 🟢 RECEBIDO
        if dtpg:
            try:
                if isinstance(dtpg, str):
                    if "/" in dtpg:
                        data_pg = datetime.strptime(dtpg, "%d/%m/%Y").date()
                    else:
                        data_pg = datetime.strptime(dtpg, "%Y-%m-%d").date()
                else:
                    data_pg = dtpg

                # 🔥 FILTRO ANO ATUAL
                if data_pg.year == hoje.year:
                    recebidos += vrpg

            except:
                pass

            continue

        # tratar data
        if dtvenc:
            try:
                if isinstance(dtvenc, str):
                    if "/" in dtvenc:
                        data_venc = datetime.strptime(dtvenc, "%d/%m/%Y").date()
                    else:
                        data_venc = datetime.strptime(dtvenc, "%Y-%m-%d").date()
                else:
                    data_venc = dtvenc
            except:
                continue

            # 🔴 ATRASADO
            if data_venc < hoje:
                atrasados += valor

            # 🟡 HOJE
            elif data_venc == hoje:
                hoje_venc += valor

            # 🔵 FUTURO
            else:
                futuros += valor

    con.close()

    return {
        "recebidos": f"{recebidos:,.2f}",
        "atrasados": f"{atrasados:,.2f}",
        "hoje": f"{hoje_venc:,.2f}",
        "futuros": f"{futuros:,.2f}"
    }

def executar_query(caminho_sql):
    try:
        with open(caminho_sql, "r", encoding="utf-8") as f:
            sql = f.read()

        con = conectar()
        cur = con.cursor()
        cur.execute(sql)

        colunas = [desc[0].lower() for desc in cur.description]

        dados = []
        for row in cur.fetchall():
            dados.append(dict(zip(colunas, row)))

        con.close()
        return dados

    except Exception as e:
        print(f"Erro ao executar {caminho_sql}: {e}")
        return []
    
    
def resumo_financeiro(data_ini, data_fim, empresas):

    con = conectar()
    cur = con.cursor()

    filtro = montar_filtro(empresas)

    sql = f"""
    SELECT dtvenc, dtpg, valor
    FROM movcp m
    LEFT JOIN cadfir f ON f.codfir = m.codfir
    WHERE m.dtvenc BETWEEN '{data_ini}' AND '{data_fim}'
    {filtro}
    """

    cur.execute(sql)

    hoje = date.today()

    pagos = atrasados = hoje_venc = futuros = 0

    for dtvenc, dtpg, valor in cur.fetchall():

        valor = float(valor or 0)

        if dtpg:
            pagos += valor
            continue

        if dtvenc:
            if dtvenc < hoje:
                atrasados += valor
            elif dtvenc == hoje:
                hoje_venc += valor
            else:
                futuros += valor

    con.close()

    return {
        "pagos": f"{pagos:,.2f}",
        "atrasados": f"{atrasados:,.2f}",
        "hoje": f"{hoje_venc:,.2f}",
        "futuros": f"{futuros:,.2f}"
    }

def listar_clientes():

    con = conectar()
    cur = con.cursor()

    cur.execute("""
        SELECT DISTINCT firma
        FROM cadcli
        WHERE firma IS NOT NULL
        ORDER BY firma
    """)

    clientes = [row[0] for row in cur.fetchall()]

    con.close()

    return clientes


def listar_empresas():

    con = conectar()
    cur = con.cursor()

    cur.execute("""
        SELECT DISTINCT firma
        FROM cadfir
        WHERE firma IS NOT NULL
        ORDER BY firma
    """)

    empresas = [row[0] for row in cur.fetchall()]

    con.close()

    return empresas

def fluxo_mensal(data_ini, data_fim, empresas):
    filtro = montar_filtro(empresas)

    con = conectar()
    cur = con.cursor()

    sql = f"""
    SELECT
        EXTRACT(MONTH FROM dtpg) AS mes,
        SUM(COALESCE(vrpg, 0)) AS recebido
    FROM movcr m
    LEFT JOIN cadfir f ON f.codfir = m.codfir
    WHERE dtpg IS NOT NULL
    AND EXTRACT(YEAR FROM dtpg) = EXTRACT(YEAR FROM CURRENT_DATE)
    AND dtpg BETWEEN '{data_ini}' AND '{data_fim}'
    {filtro}
    GROUP BY mes
    """

    cur.execute(sql)

    recebidos = {i: 0 for i in range(1, 13)}

    for mes, valor in cur.fetchall():
        recebidos[int(mes)] = float(valor or 0)

    # PAGOS
    sql = f"""
    SELECT
        EXTRACT(MONTH FROM dtpg) AS mes,
        SUM(COALESCE(valor, 0)) AS pago
    FROM movcp m
    LEFT JOIN cadfir f ON f.codfir = m.codfir
    WHERE dtpg IS NOT NULL
      AND EXTRACT(YEAR FROM dtpg) = EXTRACT(YEAR FROM CURRENT_DATE)
      AND dtpg BETWEEN '{data_ini}' AND '{data_fim}'
    {filtro}
    GROUP BY mes
    """

    cur.execute(sql)

    pagos = {i: 0 for i in range(1, 13)}

    for mes, valor in cur.fetchall():
        pagos[int(mes)] = float(valor or 0)

    con.close()

    # transforma em lista (jan → dez)
    lista_recebidos = [recebidos[i] for i in range(1, 13)]
    lista_pagos = [pagos[i] for i in range(1, 13)]

    return lista_recebidos, lista_pagos

def previsao_mensal(data_ini, data_fim, empresas):
    filtro = montar_filtro(empresas)

    con = conectar()
    cur = con.cursor()
  

    sql = f"""
    SELECT
        EXTRACT(MONTH FROM dtvenc) AS mes,
        SUM(COALESCE(valor, 0)) AS total
    FROM movcr m
    LEFT JOIN cadfir f ON f.codfir = m.codfir
    WHERE dtpg IS NULL
      AND dtvenc IS NOT NULL
      AND EXTRACT(YEAR FROM dtvenc) = EXTRACT(YEAR FROM CURRENT_DATE)
      AND m.dtvenc BETWEEN '{data_ini}' AND '{data_fim}'
    {filtro}
     GROUP BY mes
    """

    cur.execute(sql)

    previsao = {i: 0 for i in range(1, 13)}

    for mes, valor in cur.fetchall():
        previsao[int(mes)] = float(valor or 0)

    con.close()

    return [previsao[i] for i in range(1, 13)]

def previsao_receber_mensal(data_ini, data_fim, empresas):
    filtro = montar_filtro(empresas)

    con = conectar()
    cur = con.cursor()

    sql = f"""
    SELECT
        EXTRACT(MONTH FROM dtvenc) AS mes,
        SUM(COALESCE(valor, 0))
    FROM movcr m
    LEFT JOIN cadfir f ON f.codfir = m.codfir
    WHERE dtvenc IS NOT NULL
      AND EXTRACT(YEAR FROM dtvenc) = EXTRACT(YEAR FROM CURRENT_DATE)
    
   
    AND m.dtvenc BETWEEN '{data_ini}' AND '{data_fim}'
    {filtro}
    GROUP BY mes
    """

    cur.execute(sql)
    

    dados = {i: 0 for i in range(1, 13)}

    for mes, valor in cur.fetchall():
        dados[int(mes)] = float(valor or 0)

    con.close()

    return [dados[i] for i in range(1, 13)]

def previsao_pagar_mensal(data_ini, data_fim, empresas):
    filtro = montar_filtro(empresas)

    con = conectar()
    cur = con.cursor()

    sql = f"""
    SELECT
        EXTRACT(MONTH FROM dtvenc) AS mes,
        SUM(COALESCE(valor, 0))
    FROM movcp m
    LEFT JOIN cadfir f ON f.codfir = m.codfir
    WHERE dtvenc IS NOT NULL
      AND EXTRACT(YEAR FROM dtvenc) = EXTRACT(YEAR FROM CURRENT_DATE)
    
    
    AND m.dtvenc BETWEEN '{data_ini}' AND '{data_fim}'
    {filtro}
    GROUP BY mes
    """

    cur.execute(sql)
    
    

    dados = {i: 0 for i in range(1, 13)}

    for mes, valor in cur.fetchall():
        dados[int(mes)] = float(valor or 0)

    con.close()

    return [dados[i] for i in range(1, 13)]

@app.route("/")
def index():

    arquivos = os.listdir(PASTA_RELATORIOS)

    relatorios = [
        arquivo.replace(".sql", "")
        for arquivo in arquivos if arquivo.endswith(".sql")
    ]

    data_ini = request.args.get("data_ini")
    data_fim = request.args.get("data_fim")
    empresas = request.args.getlist("empresa")

    if not data_ini:
        data_ini = (date.today() - timedelta(days=30)).isoformat()

    if not data_fim:
        data_fim = date.today().isoformat()

    # 🔹 LISTA DE EMPRESAS
    empresas_lista = listar_empresas()

    resumo_pagar = resumo_financeiro(data_ini, data_fim, empresas)
    resumo_receber_dados = resumo_receber(data_ini, data_fim, empresas)

    recebidos_mensal, pagos_mensal = fluxo_mensal(data_ini, data_fim, empresas)

    previsao_mensal_dados = previsao_mensal(data_ini, data_fim, empresas)
    previsao_receber = previsao_receber_mensal(data_ini, data_fim, empresas)
    previsao_pagar = previsao_pagar_mensal(data_ini, data_fim, empresas)

    vendas = vendas_mensal(data_ini, data_fim, empresas)

    return render_template(
        "index.html",
        relatorios=relatorios,
        mostrar_voltar=False,
        resumo=resumo_pagar,
        resumo_receber=resumo_receber_dados,
        data_hoje=date.today(),
        recebidos_mensal=recebidos_mensal,
        pagos_mensal=pagos_mensal,
        previsao_mensal=previsao_mensal_dados,
        previsao_receber=previsao_receber,
        previsao_pagar=previsao_pagar,
        vendas=vendas,
        data_ini=data_ini,
        data_fim=data_fim,
        empresas_lista=empresas_lista,
        empresas_selecionadas=empresas
        
        
    )

@app.route("/relatorio/<nome>")
def relatorio(nome):
    config = CONFIG_FILTROS.get(nome, {})
    arquivos = os.listdir(PASTA_RELATORIOS)

    relatorios = [
    arq.replace(".sql", "")
    for arq in arquivos if arq.endswith(".sql")]

    estoque_negativo = request.args.get("estoque_negativo")
    
    data_ini = request.args.get("data_ini")
    data_fim = request.args.get("data_fim")
    
    cliente = request.args.get("cliente")
    empresa = request.args.getlist("empresa")
    
    cliente_param = f"%{cliente}%" if cliente else None
    empresa_param = f"%{empresa}%" if empresa else None

    caminho_sql = f"relatorios/{nome}.sql"

    with open(caminho_sql, "r", encoding="utf-8") as f:
        sql = f.read()

    if config.get("usar_tipo_data", True):
        tipo_data = request.args.get("tipo_data", "emissao")

        if tipo_data == "vencimento":
            campo_data = "dtvenc"
        elif tipo_data == "pagamento":
            campo_data = "dtpg"
        else:
            campo_data = "dtemis"
    else:
        campo_data = config.get("campo_data", "dtemis")
        tipo_data = None

    sql = sql.replace("{{campo_data}}", campo_data)
    
    if nome == "saldo_estoque" and estoque_negativo == "on":
        sql += " HAVING SUM(CASE WHEN i.tipomov = 'E' THEN i.qtdade WHEN i.tipomov = 'S' THEN -i.qtdade ELSE 0 END) < 0"

    con = conectar()
    cur = con.cursor()

    if not data_ini:
        data_ini = (date.today() - timedelta(days=30)).isoformat()

    if not data_fim:
        data_fim = date.today().isoformat()

    params = [data_ini, data_fim]

    if config.get("usar_cliente", True):
        params.extend([cliente_param, cliente_param])
    else:
        params.extend([None, None])

    if config.get("usar_empresa", True):
        params.extend([empresa_param, empresa_param])
    else:
        params.extend([None, None])

    cur.execute(sql, params)

    colunas = [desc[0].lower() for desc in cur.description]

    dados = []

    for row in cur.fetchall():

        linha = dict(zip(colunas, row))

        # trata dtvenc
        if 'dtvenc' in linha and linha['dtvenc']:
            try:
                data = datetime.strptime(linha['dtvenc'], "%d/%m/%Y").date()
                linha['dtvenc_obj'] = data
            except:
                linha['dtvenc_obj'] = None

        # trata pagamento
        if 'dtpg' in linha and linha['dtpg']:
            linha['pago'] = True
        else:
            linha['pago'] = False

        dados.append(linha)

    con.close()
    
    clientes_lista = listar_clientes()
    empresas_lista = listar_empresas()
    resumo_pagar = resumo_financeiro(data_ini, data_fim, [])
    resumo_receber_dados = resumo_receber(data_ini, data_fim, [])

    return render_template(
        "relatorios/relatorio.html",
        dados=dados,
        colunas=colunas,
        titulo=nome.upper(),
        data_ini=data_ini,
        data_fim=data_fim,
        mostrar_voltar=True,
        data_hoje=date.today(),
        tipo_data=tipo_data,
        cliente=cliente,
        empresa=empresa,
        clientes_lista=clientes_lista,
        empresas_lista=empresas_lista,
        relatorios=relatorios,
        tipo_relatorio=nome,
        resumo_pagar=resumo_pagar,
        resumo_receber=resumo_receber_dados,
        config=config,
              
        
        
        empresas_selecionadas=empresa,      
       
        
        
        
    )
    
@app.route("/dashboard/financeiro")
def dashboard_financeiro():

    data_ini = request.args.get("data_ini")
    data_fim = request.args.get("data_fim")
    empresas = request.args.getlist("empresa")

    if not data_ini:
        data_ini = (date.today() - timedelta(days=30)).isoformat()

    if not data_fim:
        data_fim = date.today().isoformat()

    # 🔹 Valores principais
    conciliado = total_conciliado(data_ini, data_fim, empresas)
    pendente = total_pendente(data_ini, data_fim, empresas)

    # 🔹 Converter para float
    conciliado_val = float(str(conciliado).replace(',', ''))
    pendente_val = float(str(pendente).replace(',', ''))

    saldo_val = conciliado_val + pendente_val
    saldo = f"{saldo_val:,.2f}"

    # 🔹 Gráficos
    planos, entrada, saida = dados_plano()
    bancos, valores_banco = dados_banco(data_ini, data_fim, empresas)
    meses_entrada, meses_saida = fluxo_mensal(data_ini, data_fim, empresas)
    
    # 🔹 LISTA DE EMPRESAS
    empresas_lista = listar_empresas()

    return render_template(
        "dashboards/financeiro.html",
        saldo=saldo,
        conciliado=conciliado,
        pendente=pendente,

        data_ini=data_ini,
        data_fim=data_fim,
        empresas_selecionadas=empresas,

        planos=planos,
        entrada=entrada,
        saida=saida,
        empresas_lista=empresas_lista,
        
        bancos=bancos,
        valores_banco=valores_banco,

        meses_entrada=meses_entrada,
        meses_saida=meses_saida
    )
    
@app.route("/api/followup")
def buscar_followup():
    clas = request.args.get("clas")
    ncont = request.args.get("ncont")

    con = conectar()
    cur = con.cursor()

    sql = """
        SELECT nomenf, obs
        FROM movflupc
        WHERE clas = ? AND ncont = ?
    """

    cur.execute(sql, (clas, ncont))
    rows = cur.fetchall()

    resultado = [
        {"nomenf": r[0], "obs": r[1]}
        for r in rows
    ]

    con.close()

    return {"dados": resultado}


  
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    
    
    
