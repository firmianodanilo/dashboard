SELECT
    m.clas,
    m.ncont,

    COALESCE(f.firma, '') AS fornecedor,

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

    m.valor,

    CASE 
        WHEN m.dtpg IS NULL THEN ''
        ELSE 
            LPAD(EXTRACT(DAY FROM m.dtpg),2,'0') || '/' ||
            LPAD(EXTRACT(MONTH FROM m.dtpg),2,'0') || '/' ||
            EXTRACT(YEAR FROM m.dtpg)
    END AS dtpg,

    'R$ ' || CAST(COALESCE(m.vrpg,0) AS DECIMAL(15,2)),

    CAST(p.descr AS VARCHAR(200) CHARACTER SET UTF8) AS plano_contas

FROM movcp m

LEFT JOIN cadfor f ON f.codfor = m.codfor
LEFT JOIN cadplb p ON p.codpla = m.codpla

WHERE {{campo_data}} IS NOT NULL
AND {{campo_data}} BETWEEN ? AND ?