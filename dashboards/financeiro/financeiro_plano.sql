SELECT 
    p.descr AS plano,

    SUM(CASE WHEN m.tipomov = 'E' THEN m.valor ELSE 0 END) AS entradas,
    SUM(CASE WHEN m.tipomov = 'S' THEN m.valor ELSE 0 END) AS saidas

FROM movban m
LEFT JOIN cadplb p ON p.codpla = m.codpla

GROUP BY p.descr

HAVING 
    SUM(CASE WHEN m.tipomov = 'E' THEN m.valor ELSE 0 END) <> 0
    OR
    SUM(CASE WHEN m.tipomov = 'S' THEN m.valor ELSE 0 END) <> 0

WHERE dtvenc BETWEEN ? AND ?
{{filtro_empresa}}