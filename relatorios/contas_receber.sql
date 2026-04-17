SELECT 

    t.codtipd as Documento,
    m.ncont as Num_Doc,
    c.firma as Cliente,

    CASE 
        WHEN m.dtemis IS NULL THEN ''
        ELSE 
            LPAD(EXTRACT(DAY FROM m.dtemis),2,'0') || '/' ||
            LPAD(EXTRACT(MONTH FROM m.dtemis),2,'0') || '/' ||
            EXTRACT(YEAR FROM m.dtemis)
    END AS dtemis,

    CASE 
        WHEN m.dtvenc IS NULL THEN ''
        ELSE 
            LPAD(EXTRACT(DAY FROM m.dtvenc),2,'0') || '/' ||
            LPAD(EXTRACT(MONTH FROM m.dtvenc),2,'0') || '/' ||
            EXTRACT(YEAR FROM m.dtvenc)
    END AS dtvenc,

    m.valor as Valor,

    CASE 
        WHEN m.dtpg IS NULL THEN ''
        ELSE 
            LPAD(EXTRACT(DAY FROM m.dtpg),2,'0') || '/' ||
            LPAD(EXTRACT(MONTH FROM m.dtpg),2,'0') || '/' ||
            EXTRACT(YEAR FROM m.dtpg)
    END AS dtpg,

    COALESCE(CAST(m.vrpg AS VARCHAR(20)), '') AS Vr_Pago,

    p.descr AS Plano_Contas,
    b.descr AS Banco

FROM movcr m

LEFT JOIN cadcli c 
    ON c.codcli = m.codcli

LEFT JOIN cadtipd t 
    ON t.codtpd = m.clas

LEFT JOIN cadplb p
    ON p.codpla = m.codpla

LEFT JOIN cadban b
    ON b.codban = m.codban

WHERE {{campo_data}} IS NOT NULL
  AND {{campo_data}} BETWEEN ? AND ?