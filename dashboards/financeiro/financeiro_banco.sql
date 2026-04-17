SELECT 
    b.descr AS banco,
    SUM(m.valor) AS total
FROM movban m
LEFT JOIN cadban b ON b.codban = m.codban
GROUP BY b.descr

WHERE dtvenc BETWEEN ? AND ?
{{filtro_empresa}}